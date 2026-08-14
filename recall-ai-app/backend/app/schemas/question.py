"""Pydantic v2 请求/响应模型。"""
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------- 错题 ----------
class QuestionCreate(BaseModel):
    """录入错题请求(拍照/截图/文本/对话四通道)。"""

    subject: str = Field("数学", description="学科(对话通道由 AI 自动识别)")
    text: str = Field(..., description="题干文本,支持 LaTeX")
    answer: str = Field("", description="正确答案")
    wrong_answer: str = Field("", description="错误作答")
    wrong_reason: str = Field("", description="错误原因(AI 自动识别)")
    source_type: Literal["text", "camera", "screenshot", "chat"] = "text"
    file_id: Optional[str] = None
    image_base64: Optional[str] = Field(None, description="拍照/截图图片 base64(可选)")


class QuestionUpdate(BaseModel):
    """编辑错题请求(可局部更新)。"""

    subject: Optional[str] = None
    text: Optional[str] = None
    answer: Optional[str] = None
    wrong_answer: Optional[str] = None
    wrong_reason: Optional[str] = None
    chapter: Optional[str] = None
    q_type: Optional[str] = None
    difficulty: Optional[str] = None


class QuestionKPOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kp_id: int
    name: str
    is_primary: bool
    confidence: float


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject: str
    chapter: str
    q_type: str
    difficulty: str
    content_json: dict
    answer: str
    wrong_answer: str
    wrong_reason: str
    ocr_status: str
    error_count: int
    created_at: datetime
    kps: list[QuestionKPOut] = []
    mastery: float = 0.0
    review_count: int = 0
    ai_summary: str = ""


class QuestionConfirm(BaseModel):
    """确认/修正知识点请求。"""

    kp_id: Optional[int] = None
    kp_name: Optional[str] = None
    confidence: float = Field(0.9, ge=0, le=1)


class MasteryUpdate(BaseModel):
    """用户主动标记掌握度(直接设置,无需经过复习自评)。"""

    status: Literal["mastered", "fuzzy", "failed"]


# ---------- 复习 ----------
class ReviewSubmit(BaseModel):
    """提交复习自评。"""

    status: Literal["mastered", "fuzzy", "failed"]
    wrong_reason: str = ""
    hint_level: int = Field(0, ge=0, le=3)
    time_cost_sec: int = Field(0, ge=0)


class ReviewSubmitOut(BaseModel):
    next_review_at: date
    trigger_variant: bool
    variant_task_id: Optional[str] = None


# ---------- AI ----------
class AIChatRequest(BaseModel):
    message: str
    question_id: Optional[int] = None


class AIChatResponse(BaseModel):
    reply: str
    sources: list[str] = []


class VariantGenerateRequest(BaseModel):
    kp_id: Optional[int] = None
    question_id: Optional[int] = None
    difficulty: Literal["easy", "mid", "hard"] = "mid"


# ---------- 分析 ----------
class KPStatOut(BaseModel):
    kp_id: int
    name: str
    mastery: float
    error_count: int


class WeeklyReportOut(BaseModel):
    total_questions: int
    review_count: int
    mastery_avg: float
    error_reasons: list[dict]
    trend: list[dict]
    weak_kps: list[KPStatOut]
    suggestions: list[str]
