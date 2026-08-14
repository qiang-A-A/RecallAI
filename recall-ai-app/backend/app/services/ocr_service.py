"""OCR 识别服务:本地 RapidOCR(onnxruntime)+ 可选 PaddleOCR-VL 外部服务。

识别流程(三级降级):
1. 本地 RapidOCR(已内置中英文模型,离线可用,主识别路径)
2. 外部 PaddleOCR-VL HTTP 服务(若配置 OCR_BASE_URL 且可达)
3. 全部失败 → 降级返回 need_manual,提示手动输入

设计目标:无 GPU、无外部依赖的环境也能真实识别图片文字。
"""
import asyncio
import logging
from pathlib import Path
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 懒加载单例(避免 import 时初始化 onnx 模型拖慢启动)
_engine = None


def _get_engine():
    """获取 RapidOCR 引擎单例(首次调用加载模型)。"""
    global _engine
    if _engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _engine = RapidOCR()
            logger.info("RapidOCR 引擎初始化成功")
        except Exception as exc:  # noqa: BLE001
            logger.warning("RapidOCR 不可用: %s", exc)
            _engine = False  # type: ignore[assignment]
    return _engine if _engine else None


class OCRService:
    """封装 OCR 能力:本地 RapidOCR 优先,外部 PaddleOCR-VL 备选。"""

    def __init__(self, base_url: str = "") -> None:
        # 外部 PaddleOCR-VL 服务地址(可选;默认从 config 读,无则仅用本地)
        self.base_url = base_url or getattr(settings, "OCR_BASE_URL", "") or "http://localhost:8001/v1/ocr"

    async def recognize(self, image_path: str | Path) -> dict[str, Any]:
        """识别一张图片,返回结构化结果。

        Args:
            image_path: 本地图片路径

        Returns:
            {"content_json": {...}, "confidence": float, "status": str}
        """
        path = Path(image_path)
        if not path.exists():
            return self._fallback("图片文件不存在,请检查路径")

        # 1) 本地 RapidOCR
        try:
            result = await self._recognize_local(path)
            local_text = (result.get("content_json") or {}).get("text", "") if result else ""
            logger.info("本地 OCR 结果: status=%s text=%r", result.get("status") if result else None, local_text[:40])
            if result and local_text:
                return result
        except Exception as exc:  # noqa: BLE001
            logger.warning("本地 OCR 失败: %s", exc)

        # 2) 外部 PaddleOCR-VL
        try:
            result = await self._recognize_remote(path)
            remote_text = (result.get("content_json") or {}).get("text", "") if result else ""
            if result and remote_text:
                return result
        except Exception as exc:  # noqa: BLE001
            logger.warning("外部 OCR 失败: %s", exc)

        return self._fallback("OCR 识别失败,请手动输入题目内容")

    async def _recognize_local(self, path: Path) -> dict[str, Any] | None:
        """本地 RapidOCR 识别(在独立线程中运行,避免阻塞事件循环)。"""
        engine = _get_engine()
        if engine is None:
            return None
        try:
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor(max_workers=1) as pool:
                res = await loop.run_in_executor(pool, lambda: engine(str(path)))
        except Exception as exc:  # noqa: BLE001
            logger.warning("RapidOCR 调用异常: %s", exc)
            return None
        # res 形如 (result, elapse) 或 (None, ...) / result: [box, text, score]
        if not res or not res[0]:
            logger.warning("RapidOCR 未识别出文本(path=%s)", path)
            return None
        lines = [str(item[1]) for item in res[0] if len(item) >= 2 and item[1]]
        text = "\n".join(lines).strip()
        if not text:
            return None
        confs = [float(item[2]) for item in res[0] if len(item) >= 3 and item[2] is not None]
        avg_conf = sum(confs) / len(confs) if confs else 0.8
        return {
            "content_json": {"text": text, "formulas": []},
            "confidence": float(avg_conf),
            "status": "processed" if avg_conf >= 0.5 else "need_review",
        }

    async def _recognize_remote(self, path: Path) -> dict[str, Any] | None:
        """外部 PaddleOCR-VL HTTP 服务识别。"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            with path.open("rb") as f:
                resp = await client.post(
                    self.base_url,
                    files={"file": (path.name, f, "image/*")},
                )
            resp.raise_for_status()
            data = resp.json()
            text = (data.get("content") or {}).get("text", "")
            if not text:
                return None
            return {
                "content_json": {"text": text, "formulas": []},
                "confidence": float(data.get("confidence", 0.8)),
                "status": "processed" if data.get("confidence", 0) >= 0.5 else "need_review",
            }

    @staticmethod
    def _fallback(reason: str) -> dict[str, Any]:
        """OCR 不可用时的降级结果。"""
        return {
            "content_json": {"text": "", "formulas": [], "error": reason},
            "confidence": 0.0,
            "status": "need_manual",
        }
