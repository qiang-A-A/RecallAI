"""用户模型:身份与学习目标,驱动推送策略与图谱初始化。"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    openid: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    identity: Mapped[str] = mapped_column(String(16), default="college")  # highschool/college/postgrad
    grade: Mapped[str] = mapped_column(String(32), default="")
    goal_subjects: Mapped[str] = mapped_column(String(128), default="数学,物理,英语")
    goal_minutes_day: Mapped[int] = mapped_column(Integer, default=15)
    onboarding_done: Mapped[bool] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
