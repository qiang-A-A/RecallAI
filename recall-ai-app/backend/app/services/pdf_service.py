"""PDF 导出服务:基于 ReportLab。

输出错题报告(PDF),支持按学科/日期范围筛选。
"""
from io import BytesIO
from pathlib import Path
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.config import get_settings

settings = get_settings()


class PDFExportService:
    """生成错题报告 PDF。"""

    def __init__(self) -> None:
        self._register_cjk_font()

    @staticmethod
    def _register_cjk_font() -> None:
        """注册中文字体,否则 PDF 中文显示为方块。

        优先用系统字体:Windows 微软雅黑 / macOS PingFang / Linux Noto。
        """
        candidates = [
            ("msyh", "C:/Windows/Fonts/msyh.ttc"),
            ("PingFang", "/System/Library/Fonts/PingFang.ttc"),
            ("NotoSansCJK", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        ]
        for name, path in candidates:
            if Path(path).exists():
                try:
                    pdfmetrics.registerFont(TTFont(name, path))
                    break
                except Exception:
                    continue

    def export_questions_pdf(
        self,
        rows: Iterable[dict],
        *,
        title: str = "Recall AI 错题报告",
        output_path: str | None = None,
    ) -> bytes:
        """导出错题列表为 PDF。

        Args:
            rows: [{subject, text, kp, status, review_count}]
            title: 报告标题
            output_path: 若指定则写文件,否则返回 bytes

        Returns:
            PDF bytes
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle("zh", fontName="msyh", fontSize=11, leading=16))
        styles.add(ParagraphStyle("zhh", fontName="msyh", fontSize=16, leading=22, spaceAfter=12))

        story = [Paragraph(title, styles["zhh"])]
        data = [["学科", "题目", "知识点", "状态", "复习次数"]]
        for r in rows:
            data.append([
                r["subject"],
                r["text"][:60],
                r["kp"],
                r["status"],
                str(r["review_count"]),
            ])
        table = Table(data, colWidths=[22 * mm, 85 * mm, 40 * mm, 20 * mm, 18 * mm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5645d4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, -1), "msyh"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(table)
        doc.build(story)

        pdf_bytes = buffer.getvalue()
        if output_path:
            Path(output_path).write_bytes(pdf_bytes)
        return pdf_bytes
