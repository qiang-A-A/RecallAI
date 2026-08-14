"""错题数据访问层:封装 SQLAlchemy 查询,业务层不直接触碰 ORM 细节。"""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.question import Question, QuestionKP, ReviewLog, ReviewState


def compute_mastery(rs: Optional[ReviewState]) -> float:
    """由 ReviewState 计算 0-100 掌握度。

    - 无 ReviewState:0.0(待掌握)
    - last_status='mastered':0.7 + min(0.3, reps*0.05) → 0.7-1.0
    - 'fuzzy':0.5(随 reps 略增)
    - 'failed':0.3
    """
    if rs is None:
        return 0.0
    base = {'mastered': 0.70, 'fuzzy': 0.50, 'failed': 0.30}.get(rs.last_status, 0.30)
    return min(1.0, base + min(0.3, (rs.reps or 0) * 0.05))


class QuestionRepository:
    """题目 + 复习状态的仓储。"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user_id: int, payload: dict) -> Question:
        q = Question(user_id=user_id, **payload)
        self.db.add(q)
        self.db.commit()
        self.db.refresh(q)
        return q

    def get(self, question_id: int, user_id: int) -> Optional[Question]:
        return self.db.execute(
            select(Question).where(
                Question.id == question_id,
                Question.user_id == user_id,
                Question.deleted_at.is_(None),
            )
        ).scalar_one_or_none()

    def list_active(
        self,
        user_id: int,
        *,
        subject: str | None = None,
        status: str | None = None,
        keyword: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[tuple[Question, float]]:
        """返回 (Question, mastery) 元组列表;mastery 由 ReviewState 计算。"""
        stmt = select(Question).where(Question.user_id == user_id, Question.deleted_at.is_(None))
        if subject:
            stmt = stmt.where(Question.subject == subject)
        if keyword:
            stmt = stmt.where(Question.content_json["text"].astext.contains(keyword))
        if status:
            # 状态通过 ReviewState 过滤(已掌握/模糊/未掌握)
            # mastery >= 70 → mastered;>= 40 → fuzzy;< 40 → 未掌握
            threshold = {'mastered': 0.7, 'fuzzy': 0.4, 'failed': 0.0}.get(status, 0.0)
            # 简化:状态过滤在 route 层做(join 后比较)
            pass
        stmt = stmt.order_by(Question.created_at.desc()).offset(offset).limit(limit)
        rows = list(self.db.execute(stmt).scalars())
        # 批量查 ReviewState
        qids = [q.id for q in rows]
        rs_map = {}
        if qids:
            for rs in self.db.execute(
                select(ReviewState).where(ReviewState.question_id.in_(qids), ReviewState.user_id == user_id)
            ).scalars():
                rs_map[rs.question_id] = rs
        return [(q, compute_mastery(rs_map.get(q.id))) for q in rows]

    def soft_delete(self, question_id: int, user_id: int) -> bool:
        q = self.get(question_id, user_id)
        if not q:
            return False
        q.deleted_at = datetime.now()
        self.db.commit()
        return True

    def increment_error(self, question_id: int) -> None:
        q = self.db.get(Question, question_id)
        if q:
            q.error_count += 1
            self.db.commit()

    # ---------- 复习状态 ----------
    def get_review_state(self, question_id: int, user_id: int) -> Optional[ReviewState]:
        return self.db.execute(
            select(ReviewState).where(
                ReviewState.question_id == question_id,
                ReviewState.user_id == user_id,
            )
        ).scalar_one_or_none()

    def upsert_review_state(self, user_id: int, question_id: int, **fields) -> ReviewState:
        rs = self.get_review_state(question_id, user_id)
        if rs is None:
            # fields 中可能含 due_date,避免与默认值冲突
            fields.setdefault("due_date", date.today())
            rs = ReviewState(user_id=user_id, question_id=question_id, **fields)
            self.db.add(rs)
        else:
            for k, v in fields.items():
                setattr(rs, k, v)
        self.db.commit()
        self.db.refresh(rs)
        return rs

    def due_questions(self, user_id: int, limit: int = 20) -> list[ReviewState]:
        """今日到期复习清单(按 due_date 升序)。"""
        stmt = (
            select(ReviewState)
            .where(ReviewState.user_id == user_id, ReviewState.due_date <= date.today())
            .order_by(ReviewState.due_date.asc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars())

    def log_review(self, user_id: int, question_id: int, **fields) -> ReviewLog:
        log = ReviewLog(user_id=user_id, question_id=question_id, **fields)
        self.db.add(log)
        self.db.commit()
        return log

    # ---------- 知识点关联 ----------
    def attach_kp(self, question_id: int, kp_id: int, confidence: float, is_primary: bool = True) -> None:
        self.db.add(QuestionKP(question_id=question_id, kp_id=kp_id, confidence=confidence, is_primary=is_primary))
        self.db.commit()

    def get_kps(self, question_id: int) -> list[QuestionKP]:
        return list(self.db.execute(
            select(QuestionKP).where(QuestionKP.question_id == question_id)
        ).scalars())
