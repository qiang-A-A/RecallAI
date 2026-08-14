"""错题模型:题目主表 + SM-2 复习状态。

content_json 用 JSONB(PostgreSQL)/ TEXT(SQLite) 存结构化题干。
"""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import JSON, Date, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    subject: Mapped[str] = mapped_column(String(16), index=True)
    chapter: Mapped[str] = mapped_column(String(64), default="")
    q_type: Mapped[str] = mapped_column(String(16), default="choice")  # choice/solve/proof/calc
    difficulty: Mapped[str] = mapped_column(String(8), default="mid")  # easy/mid/hard
    content_json: Mapped[dict] = mapped_column(JSON, default=dict)  # {text, formula, image}
    answer: Mapped[str] = mapped_column(Text, default="")
    wrong_answer: Mapped[str] = mapped_column(Text, default="")
    wrong_reason: Mapped[str] = mapped_column(String(32), default="")
    ocr_status: Mapped[str] = mapped_column(String(16), default="pending")  # pending/processed/need_review
    dedup_group_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class KnowledgePoint(Base):
    """知识图谱节点(首发覆盖数学/物理/英语)。"""

    __tablename__ = "knowledge_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject: Mapped[str] = mapped_column(String(16), index=True)
    name: Mapped[str] = mapped_column(String(64), index=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    level: Mapped[int] = mapped_column(Integer, default=2)  # 1章/2节/3考点
    exam_weight: Mapped[float] = mapped_column(Float, default=0.5)


class QuestionKP(Base):
    """题目-知识点多对多关联,含诊断置信度。"""

    __tablename__ = "question_kp"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(Integer, index=True)
    kp_id: Mapped[int] = mapped_column(Integer, index=True)
    is_primary: Mapped[bool] = mapped_column(Integer, default=1)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)


class ReviewState(Base):
    """SM-2 状态机:间隔、难度系数、下次到期日。"""

    __tablename__ = "review_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    reps: Mapped[int] = mapped_column(Integer, default=0)
    due_date: Mapped[date] = mapped_column(Date, index=True)
    last_status: Mapped[str] = mapped_column(String(8), default="fuzzy")  # mastered/fuzzy/failed
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class ReviewLog(Base):
    """复习明细日志,支撑学习分析。"""

    __tablename__ = "review_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    question_id: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[str] = mapped_column(String(8), default="fuzzy")
    time_cost_sec: Mapped[int] = mapped_column(Integer, default=0)
    hint_level_used: Mapped[int] = mapped_column(Integer, default=0)
    wrong_reason: Mapped[str] = mapped_column(String(32), default="")
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
