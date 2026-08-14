"""设置相关 API:AI 模型供应商 / API Key(运行时生效,无需重启)。"""
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import get_settings
from app.services.ai_service import AIService, get_effective_api_key, set_runtime_api_key

router = APIRouter(prefix="/settings", tags=["settings"])

app_settings = get_settings()


class ApiKeyIn(BaseModel):
    """API Key 请求体。"""

    api_key: str = Field(..., min_length=1, description="DeepSeek API Key")


class SettingsOut(BaseModel):
    """设置状态响应(不返回 key 明文)。"""

    provider: str
    model: str
    base_url: str
    api_key_configured: bool


@router.get("/ai", response_model=SettingsOut)
def get_ai_settings() -> SettingsOut:
    """查询当前 AI 设置状态(是否已配置 Key)。"""
    return SettingsOut(
        provider="DeepSeek",
        model=app_settings.DEEPSEEK_MODEL,
        base_url=app_settings.DEEPSEEK_BASE_URL,
        api_key_configured=bool(get_effective_api_key()),
    )


@router.post("/api-key", response_model=SettingsOut)
def set_api_key(body: ApiKeyIn) -> SettingsOut:
    """设置运行时 API Key(仅存内存,不落盘;重启后需重新配置或从 .env 读取)。"""
    set_runtime_api_key(body.api_key)
    return SettingsOut(
        provider="DeepSeek",
        model=app_settings.DEEPSEEK_MODEL,
        base_url=app_settings.DEEPSEEK_BASE_URL,
        api_key_configured=True,
    )


@router.delete("/api-key", response_model=SettingsOut)
def clear_api_key() -> SettingsOut:
    """清除运行时 API Key(回落到 .env 配置)。"""
    set_runtime_api_key("")
    return SettingsOut(
        provider="DeepSeek",
        model=app_settings.DEEPSEEK_MODEL,
        base_url=app_settings.DEEPSEEK_BASE_URL,
        api_key_configured=bool(app_settings.DEEPSEEK_API_KEY),
    )


class TestOut(BaseModel):
    """测试连接结果。"""

    ok: bool
    message: str


@router.post("/test", response_model=TestOut)
async def test_connection() -> TestOut:
    """向 DeepSeek 发送一条简短消息,验证 API Key 有效性。"""
    key = get_effective_api_key()
    if not key:
        raise HTTPException(status_code=400, detail="API Key 未配置,请先在设置中保存 Key")
    try:
        svc = AIService()
        url = f"{svc.base_url}/chat/completions"
        payload = {
            "model": svc.model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "ping"},
            ],
            "max_tokens": 8,
        }
        headers = {"Authorization": f"Bearer {key}"}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 401:
                return TestOut(ok=False, message="Key 无效(401 Unauthorized),请检查是否正确")
            resp.raise_for_status()
        return TestOut(ok=True, message="连接成功,API Key 有效 ✓")
    except httpx.HTTPError as e:
        return TestOut(ok=False, message=f"网络错误:{e}")
    except Exception as e:  # noqa: BLE001
        return TestOut(ok=False, message=f"测试失败:{e}")
