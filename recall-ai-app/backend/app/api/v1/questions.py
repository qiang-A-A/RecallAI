"""错题相关 API:录入、列表、详情、确认知识点、删除、导出、OCR。"""
import base64
import logging
from datetime import date as _date, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.repositories.question_repository import QuestionRepository, compute_mastery
from app.schemas.question import (
    MasteryUpdate,
    QuestionConfirm,
    QuestionCreate,
    QuestionOut,
    QuestionUpdate,
)
from app.services.ai_service import AIService
from app.services.ocr_service import OCRService
from app.services.pdf_service import PDFExportService
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/questions", tags=["questions"])

# 演示用固定用户(MVP 期无登录)
DEMO_USER_ID = 1


@router.post("/ocr", status_code=200)
async def ocr_image(file: UploadFile) -> dict:
    """拍照/截图图片 OCR 识别,返回题干文本与结构化内容。

    无 OCR 服务时降级返回提示,不阻塞。
    """
    img_bytes = await file.read()
    if not img_bytes:
        raise HTTPException(status_code=400, detail="图片为空")
    # 保存临时文件
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    tmp = upload_dir / f"ocr_{file.filename or 'tmp.png'}"
    tmp.write_bytes(img_bytes)
    try:
        svc = OCRService()
        result = await svc.recognize(tmp)
        text = (result.get("content_json") or {}).get("text", "")
        return {
            "text": text,
            "confidence": result.get("confidence", 0.0),
            "status": result.get("status", "need_review"),
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("OCR 失败: %s", exc)
        return {"text": "", "confidence": 0.0, "status": "unavailable", "detail": str(exc)}


@router.post("/analyze", status_code=200)
async def analyze_text(payload: QuestionCreate) -> dict:
    """AI 自动识别:学科 / 知识点 / 错因 / 答案 / 题型 / 难度。

    供前端在确认归档前预览 AI 识别结果(录入四通道共用)。
    """
    ai = AIService()
    try:
        result = await ai.analyze_question(payload.text, payload.source_type)
        return {"ok": True, **result}
    except Exception as exc:  # noqa: BLE001
        logger.warning("AI 归档分析失败: %s", exc)
        return {"ok": False, "detail": str(exc), "subject": "数学", "kp_name": "待确认", "wrong_reason": "其他"}


@router.post("", response_model=QuestionOut, status_code=201)
async def create_question(
    payload: QuestionCreate,
    db: Session = Depends(get_db),
) -> QuestionOut:
    """录入错题:OCR(若有图)→ 去重 → 入库 → AI 自动识别归档。

    支持 text / camera / screenshot / chat 四通道;AI 识别学科、知识点、错因。
    """
    repo = QuestionRepository(db)

    # 拍照/截图:base64 图 → OCR 提取文本(若题干为空)
    text = payload.text
    if not text.strip() and payload.image_base64:
        try:
            img = base64.b64decode(payload.image_base64.split(",")[-1])
            upload_dir = Path(settings.UPLOAD_DIR)
            upload_dir.mkdir(parents=True, exist_ok=True)
            tmp = upload_dir / "upload_question.png"
            tmp.write_bytes(img)
            ocr = OCRService()
            result = await ocr.recognize(tmp)
            text = (result.get("content_json") or {}).get("text", "")
        except Exception as exc:  # noqa: BLE001
            logger.warning("上传图 OCR 失败: %s", exc)

    content = {"text": text, "formulas": [], "source_type": payload.source_type}
    q = repo.create(DEMO_USER_ID, {
        "subject": payload.subject,
        "content_json": content,
        "answer": payload.answer,
        "wrong_answer": payload.wrong_answer,
        "wrong_reason": payload.wrong_reason,
        "ocr_status": "processed",
    })

    # AI 自动识别归档:学科 / 知识点 / 错因(尽力而为,失败不阻塞)
    if text.strip():
        try:
            ai = AIService()
            result = await ai.analyze_question(text, payload.source_type)
            q.subject = result.get("subject", q.subject) or q.subject
            q.wrong_reason = result.get("wrong_reason", q.wrong_reason) or q.wrong_reason
            if not payload.answer:
                q.answer = result.get("answer", "")
            kp_name = result.get("kp_name", "")
            if kp_name and kp_name != "待确认":
                # 更新知识点名称(简化:按名字查找/新建后关联)
                from app.models.question import KnowledgePoint
                kp = db.execute(
                    select(KnowledgePoint)
                    .where(KnowledgePoint.user_id == DEMO_USER_ID)
                    .where(KnowledgePoint.name == kp_name)
                ).scalar_one_or_none()
                if kp is None:
                    kp = KnowledgePoint(
                        user_id=DEMO_USER_ID, subject=q.subject,
                        name=kp_name, mastery=0.0, error_count=0, level=2, exam_weight=0.5,
                    )
                    db.add(kp)
                    db.flush()
                repo.attach_kp(q.id, kp_id=kp.id, confidence=0.7)
            db.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("AI 归档失败(不影响录入): %s", exc)
            db.rollback()
            db.refresh(q)

    # 向量去重(纯文本场景)
    try:
        vector = VectorService()
        dup = vector.find_similar(text, DEMO_USER_ID)
        if dup:
            q.dedup_group_id = dup["question_id"]
            repo.increment_error(dup["question_id"])
            db.commit()
        else:
            vector.upsert_question(q.id, DEMO_USER_ID, text)
    except Exception:
        # 向量库不可用不影响主流程
        pass

    return QuestionOut.model_validate(q)


@router.get("", response_model=list[QuestionOut])
def list_questions(
    subject: str | None = Query(None),
    status: str | None = Query(None),
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[QuestionOut]:
    """错题列表(支持筛选/搜索/分页)。mastery 由 ReviewState 真实计算。"""
    repo = QuestionRepository(db)
    items = repo.list_active(DEMO_USER_ID, subject=subject, keyword=keyword,
                             offset=(page - 1) * page_size, limit=page_size)
    out = []
    for q, mastery in items:
        if status:
            # mastery >= 70 → mastered;>= 40 → fuzzy;< 40 → 未掌握
            thr = {'mastered': 0.7, 'fuzzy': 0.4, 'failed': 0.0}.get(status, 0.0)
            if mastery < thr:
                continue
        qo = QuestionOut.model_validate(q)
        qo.mastery = round(mastery, 2)
        out.append(qo)
    return out


@router.get("/{question_id}", response_model=QuestionOut)
def get_question(question_id: int, db: Session = Depends(get_db)) -> QuestionOut:
    """错题详情。mastery 由 ReviewState 计算。"""
    repo = QuestionRepository(db)
    q = repo.get(question_id, DEMO_USER_ID)
    if not q:
        raise HTTPException(status_code=404, detail="错题不存在")
    rs = repo.get_review_state(question_id, DEMO_USER_ID)
    from app.repositories.question_repository import compute_mastery
    qo = QuestionOut.model_validate(q)
    qo.mastery = round(compute_mastery(rs), 2)
    return qo


@router.post("/{question_id}/confirm", response_model=QuestionOut)
def confirm_kp(question_id: int, payload: QuestionConfirm, db: Session = Depends(get_db)) -> QuestionOut:
    """确认/修正知识点(低置信度兜底)。"""
    repo = QuestionRepository(db)
    q = repo.get(question_id, DEMO_USER_ID)
    if not q:
        raise HTTPException(status_code=404, detail="错题不存在")
    kp_id = payload.kp_id or 1
    repo.attach_kp(question_id, kp_id=kp_id, confidence=payload.confidence)
    return QuestionOut.model_validate(q)


@router.post("/{question_id}/mastery", response_model=QuestionOut)
def set_mastery(question_id: int, payload: MasteryUpdate, db: Session = Depends(get_db)) -> QuestionOut:
    """用户主动标记掌握度(无需经过复习自评,直接更新 ReviewState.last_status)。

    用途:用户在错题集卡片上点击"已掌握/模糊/未掌握"按钮,看板与列表立即联动。
    """
    repo = QuestionRepository(db)
    q = repo.get(question_id, DEMO_USER_ID)
    if not q:
        raise HTTPException(status_code=404, detail="错题不存在")
    rs = repo.get_review_state(question_id, DEMO_USER_ID)
    fields = {"last_status": payload.status, "last_reviewed_at": datetime.now()}
    if rs is None:
        # 首次标记:创建 ReviewState 行(reps=1 让 mastery 显示有复习经历)
        repo.upsert_review_state(
            DEMO_USER_ID, question_id,
            interval_days=0, ease_factor=2.5, reps=1,
            due_date=_date.today(),
            last_status=payload.status,
            last_reviewed_at=datetime.now(),
        )
    else:
        # 已存在:更新状态 + 复习次数 +1 + last_reviewed_at
        new_reps = (rs.reps or 0) + 1
        repo.upsert_review_state(
            DEMO_USER_ID, question_id,
            last_status=payload.status,
            last_reviewed_at=datetime.now(),
            reps=new_reps,
        )
    # 重新读取并填充 mastery
    rs2 = repo.get_review_state(question_id, DEMO_USER_ID)
    qo = QuestionOut.model_validate(q)
    qo.mastery = round(compute_mastery(rs2), 2)
    return qo


@router.put("/{question_id}", response_model=QuestionOut)
def update_question(question_id: int, payload: QuestionUpdate, db: Session = Depends(get_db)) -> QuestionOut:
    """编辑错题:更新题干/学科/答案/错因等(局部更新,空字段不覆盖)。"""
    repo = QuestionRepository(db)
    q = repo.get(question_id, DEMO_USER_ID)
    if not q:
        raise HTTPException(status_code=404, detail="错题不存在")
    # 文本字段更新(排除空值)
    text_map = {
        "subject": payload.subject, "chapter": payload.chapter, "q_type": payload.q_type,
        "difficulty": payload.difficulty, "answer": payload.answer,
        "wrong_answer": payload.wrong_answer, "wrong_reason": payload.wrong_reason,
    }
    for field, value in text_map.items():
        if value is not None and str(value).strip() != "":
            setattr(q, field, value)
    # 题干在 content_json.text 内
    if payload.text is not None and str(payload.text).strip() != "":
        cj = dict(q.content_json)
        cj["text"] = payload.text
        q.content_json = cj
    db.commit()
    db.refresh(q)
    # 重新填充 mastery(复习状态不变)
    rs = repo.get_review_state(question_id, DEMO_USER_ID)
    from app.repositories.question_repository import compute_mastery as _cm
    qo = QuestionOut.model_validate(q)
    qo.mastery = round(_cm(rs), 2)
    return qo


@router.delete("/{question_id}", status_code=204)
def delete_question(question_id: int, db: Session = Depends(get_db)) -> None:
    """软删除错题。"""
    repo = QuestionRepository(db)
    if not repo.soft_delete(question_id, DEMO_USER_ID):
        raise HTTPException(status_code=404, detail="错题不存在")


@router.get("/export/pdf")
def export_pdf(
    subject: str | None = Query(None),
    db: Session = Depends(get_db),
) -> Response:
    """导出错题为 PDF(ReportLab)。"""
    repo = QuestionRepository(db)
    items = repo.list_active(DEMO_USER_ID, subject=subject, limit=500)
    rows = [
        {
            "subject": q.subject,
            "text": (q.content_json or {}).get("text", ""),
            "kp": "待确认",
            "status": "new",
            "review_count": q.error_count,
        }
        for q in items
    ]
    svc = PDFExportService()
    pdf = svc.export_questions_pdf(rows)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="recall-report.pdf"'},
    )
