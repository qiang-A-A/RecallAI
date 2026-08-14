"""DeepSeek LLM 服务。

职责:
- 知识点诊断(结构化 JSON 输出)
- 复习讲解(3 级提示梯度)
- 变式题生成(JSON + 质检重试)
- AI 对话

关键设计:
- 所有 LLM 输出要求 JSON,用 Pydantic 校验,失败自动重试一次
- 超时 60s 降级返回"默认考点+人工修正",不阻塞主链路
"""
import json
import logging
from typing import Any

import httpx
from pydantic import BaseModel, Field

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 运行时 API Key(用户通过设置接口注入,优先于 .env)
_runtime_api_key: str = ""


def set_runtime_api_key(key: str) -> None:
    """设置运行时 API Key(空串清除)。"""
    global _runtime_api_key
    _runtime_api_key = (key or "").strip()


def get_effective_api_key() -> str:
    """获取生效的 API Key:运行时 > .env。"""
    return _runtime_api_key or settings.DEEPSEEK_API_KEY


class DiagnosisResult(BaseModel):
    """知识点诊断结构化输出。"""

    candidates: list[dict[str, Any]] = Field(..., description="Top-3 候选知识点")
    q_type: str = "choice"
    difficulty: str = "mid"


class VariantResult(BaseModel):
    """变式题生成结果。"""

    questions: list[dict[str, Any]] = Field(..., description="1-3 道变式题")


class AIService:
    """封装 DeepSeek Chat Completions API。"""

    def __init__(self) -> None:
        self.base_url = settings.DEEPSEEK_BASE_URL
        self.model = settings.DEEPSEEK_MODEL

    @property
    def api_key(self) -> str:
        return get_effective_api_key()

    async def _chat(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """调用 DeepSeek,返回文本回复。

        Raises:
            AIUnavailableError: API Key 缺失或请求失败
        """
        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY 未配置")

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def diagnose(self, question_text: str, kp_context: list[str]) -> DiagnosisResult:
        """知识点诊断。

        Args:
            question_text: 题干
            kp_context: RAG 检索到的知识图谱上下文

        Returns:
            DiagnosisResult(含候选知识点、题型、难度)
        """
        system = (
            "你是一名学科诊断专家。给定题目与知识图谱上下文,判断考查的核心知识点。"
            '仅输出 JSON: {"candidates": [{"kp_id","name","confidence","reason"}...], "q_type":"choice|solve|proof|calc", "difficulty":"easy|mid|hard"}。'
        )
        user = f"题目:\n{question_text}\n\n图谱上下文:\n" + "\n".join(kp_context)
        raw = await self._chat(system, user)
        try:
            parsed = json.loads(raw)
            return DiagnosisResult(**parsed)
        except Exception as exc:
            logger.warning("诊断 JSON 解析失败,重试一次: %s", exc)
            # 重试一次(提高温度增加多样性)
            raw = await self._chat(system, user, temperature=0.6)
            return DiagnosisResult(**json.loads(raw))

    async def generate_hints(self, question_text: str, answer: str) -> list[str]:
        """生成 3 级提示梯度(考点→思路→解析)。"""
        system = (
            "你是耐心的高中/大学教师。为学生生成 3 级提示,从抽象到具体:"
            "①核心考点 ②思路引导 ③完整解析。"
            '仅输出 JSON: {"hints": ["考点", "思路", "解析"]}'
        )
        user = f"题目:{question_text}\n参考答案:{answer}"
        raw = await self._chat(system, user, temperature=0.4)
        data = json.loads(raw)
        hints = data.get("hints", [])
        return (hints + ["", "", ""])[:3]

    async def generate_variants(
        self,
        question_text: str,
        kp_name: str,
        difficulty: str = "mid",
        count: int = 3,
    ) -> VariantResult:
        """生成变式题(难度递增)。

        Raises:
            RuntimeError: 连续 2 次生成失败
        """
        system = (
            "你是命题专家。围绕指定知识点为原题生成变式题,难度递增。"
            "题目必须答案唯一、题干清晰、与原题同考点但不同面孔。"
            '仅输出 JSON: {"questions": [{"text","answer","difficulty","hint"}...]}'
        )
        user = f"知识点:{kp_name}\n原题:{question_text}\n难度:{difficulty}\n数量:{count}"
        raw = await self._chat(system, user, temperature=0.8)
        try:
            return VariantResult(**json.loads(raw))
        except Exception as exc:
            logger.warning("变式生成解析失败,重试: %s", exc)
            raw = await self._chat(system, user, temperature=0.9)
            return VariantResult(**json.loads(raw))

    async def analyze_question(self, text: str, source_type: str = "text") -> dict[str, Any]:
        """四通道录入统一分析:识别学科、知识点、错因、答案、题目类型。

        供拍照/截图(OCR 文本)/文本/对话 四种录入通道共用,结果用于自动归档。
        """
        system = (
            "你是 Recall AI 的智能归档引擎。根据学生提供的题目内容,自动完成结构化识别。"
            "输出严格 JSON,不要其他文字:"
            '{"subject":"数学|物理|化学|生物|英语|语文|其他","q_type":"choice|solve|proof|calc|other",'
            '"difficulty":"easy|mid|hard","kp_name":"核心知识点名称",'
            '"answer":"参考答案","wrong_reason":"最可能的错误原因(概念混淆/计算失误/审题偏差/方法不熟/其他)",'
            '"reason":"一句话说明为什么这样归类"}'
        )
        user = f"来源方式: {source_type}\n题目内容:\n{text}"
        raw = await self._chat(system, user, temperature=0.2, max_tokens=1024)
        try:
            data = json.loads(raw)
        except Exception as exc:
            logger.warning("归档分析 JSON 解析失败: %s", exc)
            data = {"subject": "数学", "kp_name": "待确认", "wrong_reason": "其他"}
        return {
            "subject": str(data.get("subject", "数学")),
            "q_type": str(data.get("q_type", "choice")),
            "difficulty": str(data.get("difficulty", "mid")),
            "kp_name": str(data.get("kp_name", "待确认")),
            "answer": str(data.get("answer", "")),
            "wrong_reason": str(data.get("wrong_reason", "其他")),
            "reason": str(data.get("reason", "")),
        }

    async def chat(self, message: str, question_context: str = "") -> str:
        """AI 对话(答疑)。"""
        system = (
            "你是 Recall AI 学习助手,面向高中/大学/考研学生。"
            "回答要分步、可理解,先引导思考再给结论,避免直接贴答案。"
            '当需要结构化输出时用 JSON;一般对话用自然文本。'
        )
        user = f"题目上下文:{question_context}\n\n学生提问:{message}" if question_context else message
        # 对话场景不需要强制 JSON
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.6,
            "max_tokens": 2048,
        }
        async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                url, json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
