"""复习相关 API:今日清单、提交自评、变式触发。"""
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.question_repository import QuestionRepository
from app.schemas.question import ReviewSubmit, ReviewSubmitOut
from app.services.review_service import ReviewService, SM2State

router = APIRouter(prefix="/reviews", tags=["reviews"])

DEMO_USER_ID = 1

STATUS_GRADE = {"failed": 0, "fuzzy": 1, "mastered": 2}


@router.get("/today")
def today_review(db: Session = Depends(get_db)) -> dict:
    """今日到期复习清单。"""
    repo = QuestionRepository(db)
    due = repo.due_questions(DEMO_USER_ID)
    items = []
    for rs in due:
        q = repo.get(rs.question_id, DEMO_USER_ID)
        items.append({
            "question_id": rs.question_id,
            "due_date": str(rs.due_date),
            "status": rs.last_status,
            "interval_days": rs.interval_days,
            "content_text": (q.content_json.get("text", "") if q else ""),
            "subject": (q.subject if q else ""),
        })
    return {"count": len(items), "items": items}


@router.post("/{question_id}/submit", response_model=ReviewSubmitOut)
def submit_review(
    question_id: int,
    payload: ReviewSubmit,
    db: Session = Depends(get_db),
) -> ReviewSubmitOut:
    """提交复习自评,更新 SM-2 状态。

    Returns:
        下次复习日期 + 是否触发变式训练
    """
    repo = QuestionRepository(db)
    q = repo.get(question_id, DEMO_USER_ID)
    if not q:
        raise HTTPException(status_code=404, detail="错题不存在")

    # SM-2 更新
    rs = repo.get_review_state(question_id, DEMO_USER_ID)
    state = SM2State(
        interval_days=rs.interval_days if rs else 0,
        ease_factor=rs.ease_factor if rs else 2.5,
        reps=rs.reps if rs else 0,
    )
    next_due = ReviewService().next_due(STATUS_GRADE[payload.status], state)
    repo.upsert_review_state(
        DEMO_USER_ID, question_id,
        interval_days=state.interval_days,
        ease_factor=state.ease_factor,
        reps=state.reps,
        due_date=next_due,
        last_status=payload.status,
        last_reviewed_at=datetime.now(),
    )
    # 复习日志
    repo.log_review(
        DEMO_USER_ID, question_id,
        status=payload.status,
        wrong_reason=payload.wrong_reason,
        hint_level_used=payload.hint_level,
        time_cost_sec=payload.time_cost_sec,
    )

    # 变式触发判定:模糊/不会 ≥ 2 次(简化:本次 fuzzy/failed 即触发)
    trigger = payload.status in {"fuzzy", "failed"}
    return ReviewSubmitOut(
        next_review_at=next_due,
        trigger_variant=trigger,
        variant_task_id=f"vt_{question_id}" if trigger else None,
    )
