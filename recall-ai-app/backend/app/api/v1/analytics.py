"""数据分析 API:周报、掌握度矩阵、错因分布。"""
from collections import Counter
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.question import Question, ReviewLog, ReviewState
from app.repositories.question_repository import compute_mastery
from app.schemas.question import WeeklyReportOut

router = APIRouter(prefix="/analytics", tags=["analytics"])

DEMO_USER_ID = 1


@router.get("/weekly", response_model=WeeklyReportOut)
def weekly_report(db: Session = Depends(get_db)) -> WeeklyReportOut:
    """生成周报:总数、复习量、掌握度、错因 TOP5、趋势、薄弱考点、建议。"""
    week_ago = date.today() - timedelta(days=7)

    total = db.execute(
        select(Question).where(Question.user_id == DEMO_USER_ID, Question.deleted_at.is_(None))
    ).scalars().all()

    logs = db.execute(
        select(ReviewLog).where(
            ReviewLog.user_id == DEMO_USER_ID,
            ReviewLog.reviewed_at >= week_ago,  # type: ignore[operator]
        )
    ).scalars().all()

    states = db.execute(
        select(ReviewState).where(ReviewState.user_id == DEMO_USER_ID)
    ).scalars().all()

    # 错因 TOP5
    reasons = Counter((log.wrong_reason or "未标记") for log in logs)
    error_reasons = [{"reason": k, "count": v} for k, v in reasons.most_common(5)]

    # 掌握度平均:按全部错题 join ReviewState 计算的 mastery 加权
    if total:
        rs_map = {rs.question_id: rs for rs in states}
        ms = [compute_mastery(rs_map.get(q.id)) for q in total]
        mastery_avg = round(sum(ms) / len(ms) * 100, 1) if ms else 0.0
    else:
        mastery_avg = 0.0

    # 近 7 天趋势(每日复习量)
    trend_map: dict[str, int] = {}
    for log in logs:
        day = str(log.reviewed_at.date())
        trend_map[day] = trend_map.get(day, 0) + 1
    trend = [{"date": str(week_ago + timedelta(days=i)), "count": trend_map.get(str(week_ago + timedelta(days=i)), 0)} for i in range(8)]

    # 薄弱考点:mastery < 0.4 且 error_count >= 2
    weak_kps = []
    if total:
        rs_map = {rs.question_id: rs for rs in states}
        # 简化:按学科 + 平均 mastery 统计
        subj_ms: dict[str, list[float]] = {}
        for q in total:
            subj_ms.setdefault(q.subject, []).append(compute_mastery(rs_map.get(q.id)))
        for subj, ms in subj_ms.items():
            avg = sum(ms) / len(ms)
            if avg < 0.5 and len(total) >= 2:
                weak_kps.append({"kp_id": 0, "name": f"{subj}(综合掌握度{int(avg * 100)}%)", "mastery": avg, "error_count": len([m for m in ms if m < 0.4])})

    suggestions = []
    if mastery_avg < 60:
        suggestions.append("整体掌握度偏低,建议增加每日复习量并优先强化薄弱考点。")
    if reasons:
        top = error_reasons[0]["reason"]
        suggestions.append(f"本周最高频错因是「{top}」,建议针对性训练。")
    suggestions.append("连续打卡 7 天可解锁「高效学习」徽章。")

    return WeeklyReportOut(
        total_questions=len(total),
        review_count=len(logs),
        mastery_avg=mastery_avg,
        error_reasons=error_reasons,
        trend=trend,
        weak_kps=weak_kps,
        suggestions=suggestions,
    )
