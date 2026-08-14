"""SM-2 间隔重复算法与复习调度服务。

算法来源:Anki 使用的简化 SM-2,配合 Recall 的优先级权重。
"""
import math
from datetime import date, timedelta

from app.config import get_settings

settings = get_settings()


class SM2State:
    """SM-2 状态封装。"""

    def __init__(self, interval_days: int = 0, ease_factor: float = 2.5, reps: int = 0) -> None:
        self.interval_days = interval_days
        self.ease_factor = ease_factor
        self.reps = reps

    def update(self, grade: int) -> None:
        """按自评等级更新状态。

        Args:
            grade: 0=不会(failed) 1=模糊(fuzzy) 2=已掌握(mastered)
        """
        if grade == 0:
            self.reps = 0
            self.interval_days = 1
            self.ease_factor = max(1.3, self.ease_factor - 0.2)
        elif grade == 1:
            self.reps += 1
            self.interval_days = 1
        else:
            self.reps += 1
            if self.reps == 1:
                self.interval_days = 1
            elif self.reps == 2:
                self.interval_days = 3
            else:
                self.interval_days = round(self.interval_days * self.ease_factor)
            self.ease_factor = min(2.8, self.ease_factor + 0.1)


class ReviewService:
    """复习调度:每日清单生成 + SM-2 更新 + 倦怠保护。"""

    def __init__(self) -> None:
        self.limit = settings.DAILY_REVIEW_LIMIT

    def next_due(self, grade: int, state: SM2State) -> date:
        """计算下次复习日期。"""
        state.update(grade)
        return date.today() + timedelta(days=state.interval_days)

    def compute_priority(
        self,
        *,
        exam_days: int | None,
        error_freq: float,
        kp_weakness: float,
        overdue_days: int,
    ) -> float:
        """复习优先级权重,越大越优先。

        Args:
            exam_days: 距考试天数(None=无考试目标)
            error_freq: 错误次数/复习次数
            kp_weakness: 考点薄弱度(0-1, 1=最弱)
            overdue_days: 逾期天数

        Returns:
            0-1 优先级分数
        """
        exam_proximity = 0.0
        if exam_days is not None:
            exam_proximity = min(1.0, max(0.0, (7 - exam_days) / 7))  # 考前 7 天封顶
        return (
            0.40 * exam_proximity
            + 0.30 * min(1.0, error_freq)
            + 0.20 * kp_weakness
            + 0.10 * min(1.0, overdue_days / 7)
        )

    def is_bored(self, days_without_review: int) -> bool:
        """学习倦怠判定:连续 N 天未复习。"""
        return days_without_review >= settings.BORED_DAYS
