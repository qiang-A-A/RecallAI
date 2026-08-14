"""AI 相关 API:对话、变式生成。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.question_repository import QuestionRepository
from app.schemas.question import (
    AIChatRequest,
    AIChatResponse,
    VariantGenerateRequest,
)
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])

DEMO_USER_ID = 1


@router.post("/chat", response_model=AIChatResponse)
async def chat(payload: AIChatRequest, db: Session = Depends(get_db)) -> AIChatResponse:
    """AI 答疑对话。若携带 question_id 则附带题目上下文。"""
    context = ""
    if payload.question_id:
        repo = QuestionRepository(db)
        q = repo.get(payload.question_id, DEMO_USER_ID)
        if q:
            context = (q.content_json or {}).get("text", "")

    try:
        ai = AIService()
        reply = await ai.chat(payload.message, question_context=context)
        return AIChatResponse(reply=reply, sources=[context] if context else [])
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI 服务暂不可用: {exc}")


@router.post("/variant/generate")
async def generate_variant(
    payload: VariantGenerateRequest,
    db: Session = Depends(get_db),
) -> dict:
    """生成变式题。"""
    repo = QuestionRepository(db)
    if payload.question_id:
        q = repo.get(payload.question_id, DEMO_USER_ID)
        if not q:
            raise HTTPException(status_code=404, detail="错题不存在")
        question_text = (q.content_json or {}).get("text", "")
        kp_name = "待确认"
    else:
        question_text, kp_name = "知识点专项练习", payload.kp_id and "知识点" or "综合"

    try:
        ai = AIService()
        result = await ai.generate_variants(question_text, kp_name, payload.difficulty)
        return {"task_id": f"vt_{payload.question_id or 'gen'}", "questions": result.questions}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"变式生成失败: {exc}")
