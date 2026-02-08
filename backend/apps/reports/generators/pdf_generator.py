"""
PDF Report Generator for ARIZ sessions.

Uses ReportLab to generate PDF documents with full Cyrillic support
via DejaVu Sans font. Report structure:
  Title page -> Problem description -> Steps by parts -> Solutions with scores.
"""
import io
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


# ---------------------------------------------------------------------------
# Cyrillic font registration
# ---------------------------------------------------------------------------

_FONT_REGISTERED = False
_BASE_FONT = "DejaVuSans"
_BOLD_FONT = "DejaVuSans-Bold"


def _register_cyrillic_fonts():
    """Register DejaVu Sans fonts for Cyrillic support.

    Searches common system paths and a bundled ``fonts/`` directory.
    Falls back to Helvetica if DejaVu Sans is not found (Cyrillic will not
    render correctly in that case, but the generator will not crash).
    """
    global _FONT_REGISTERED, _BASE_FONT, _BOLD_FONT
    if _FONT_REGISTERED:
        return

    font_dirs = [
        # Linux (Debian/Ubuntu)
        "/usr/share/fonts/truetype/dejavu",
        # Linux (Alpine / Docker)
        "/usr/share/fonts/dejavu",
        # macOS Homebrew (Intel)
        "/usr/local/share/fonts",
        # macOS Homebrew (Apple Silicon)
        "/opt/homebrew/share/fonts",
        # Bundled in the app
        os.path.join(os.path.dirname(__file__), "..", "fonts"),
    ]

    font_path = None
    font_bold_path = None

    for directory in font_dirs:
        candidate = os.path.join(directory, "DejaVuSans.ttf")
        candidate_bold = os.path.join(directory, "DejaVuSans-Bold.ttf")
        if os.path.isfile(candidate):
            font_path = candidate
            font_bold_path = candidate_bold if os.path.isfile(candidate_bold) else candidate
            break

    if font_path:
        pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", font_bold_path))
    else:
        _BASE_FONT = "Helvetica"
        _BOLD_FONT = "Helvetica-Bold"

    _FONT_REGISTERED = True


def _build_styles():
    """Build custom paragraph styles for the report."""
    _register_cyrillic_fonts()
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "TitlePage",
        parent=styles["Title"],
        fontName=_BOLD_FONT,
        fontSize=26,
        leading=32,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.HexColor("#1a237e"),
    ))
    styles.add(ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontName=_BASE_FONT,
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=10,
        textColor=colors.HexColor("#546e7a"),
    ))
    styles.add(ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading1"],
        fontName=_BOLD_FONT,
        fontSize=18,
        leading=22,
        spaceBefore=20,
        spaceAfter=12,
        textColor=colors.HexColor("#1a237e"),
    ))
    styles.add(ParagraphStyle(
        "PartHeading",
        parent=styles["Heading2"],
        fontName=_BOLD_FONT,
        fontSize=14,
        leading=17,
        spaceBefore=14,
        spaceAfter=8,
        textColor=colors.HexColor("#283593"),
    ))
    styles.add(ParagraphStyle(
        "BodyReport",
        parent=styles["Normal"],
        fontName=_BASE_FONT,
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        "StepTitle",
        parent=styles["Normal"],
        fontName=_BOLD_FONT,
        fontSize=11,
        leading=14,
        spaceBefore=10,
        spaceAfter=4,
        textColor=colors.HexColor("#37474f"),
    ))
    styles.add(ParagraphStyle(
        "LabelStyle",
        parent=styles["Normal"],
        fontName=_BOLD_FONT,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#455a64"),
    ))
    styles.add(ParagraphStyle(
        "SmallText",
        parent=styles["Normal"],
        fontName=_BASE_FONT,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#78909c"),
    ))
    styles.add(ParagraphStyle(
        "TableHeaderStyle",
        parent=styles["Normal"],
        fontName=_BOLD_FONT,
        fontSize=10,
        leading=12,
        alignment=TA_LEFT,
        textColor=colors.white,
    ))
    styles.add(ParagraphStyle(
        "TableCellStyle",
        parent=styles["Normal"],
        fontName=_BASE_FONT,
        fontSize=9,
        leading=12,
    ))
    styles.add(ParagraphStyle(
        "ScoreHigh",
        parent=styles["Normal"],
        fontName=_BOLD_FONT,
        fontSize=10,
        textColor=colors.HexColor("#2e7d32"),
    ))
    styles.add(ParagraphStyle(
        "ScoreMedium",
        parent=styles["Normal"],
        fontName=_BOLD_FONT,
        fontSize=10,
        textColor=colors.HexColor("#ef6c00"),
    ))
    styles.add(ParagraphStyle(
        "ScoreLow",
        parent=styles["Normal"],
        fontName=_BOLD_FONT,
        fontSize=10,
        textColor=colors.HexColor("#c62828"),
    ))

    return styles


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODE_LABELS = {
    "express": "Краткий АРИЗ (Экспресс)",
    "full": "Полный АРИЗ-2010",
    "autopilot": "Автопилот",
}

FULL_ARIZ_PARTS = {
    1: "Часть 1: Анализ задачи",
    2: "Часть 2: Анализ ресурсов",
    3: "Часть 3: Определение ОП и ИКР",
    4: "Часть 4: Мобилизация и применение ВПР",
}

EXPRESS_LABELS = {
    "1": "Формулировка задачи",
    "2": "Поверхностное противоречие",
    "3": "Углублённое противоречие",
    "4": "Идеальный конечный результат",
    "5": "Обострённое противоречие",
    "6": "Углубление ОП",
    "7": "Решение",
}

DOMAIN_LABELS = {
    "technical": "Техническая",
    "business": "Бизнес",
    "everyday": "Бытовая",
}

METHOD_LABELS = {
    "principle": "Приём ТРИЗ",
    "standard": "Стандарт",
    "effect": "Эффект",
    "analog": "Аналог",
    "combined": "Комбинированный",
}

CONTRADICTION_TYPE_LABELS = {
    "surface": "Поверхностное (ПП)",
    "deepened": "Углублённое (УП)",
    "sharpened": "Обострённое (ОП)",
}


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class PDFReportGenerator:
    """Generates a PDF report for a completed ARIZ session.

    Usage::

        generator = PDFReportGenerator(session)
        pdf_bytes = generator.generate()
    """

    def __init__(self, session):
        """Initialize with an ``ARIZSession`` instance."""
        self.session = session
        self.problem = session.problem
        self.styles = _build_styles()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self) -> bytes:
        """Generate the PDF and return raw bytes."""
        buffer = io.BytesIO()

        doc = BaseDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            title=f"АРИЗ-отчёт: {self.problem.title}",
            author="ТРИЗ-Решатель",
        )

        frame_title = Frame(
            doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
            id="title_frame",
        )
        frame_content = Frame(
            doc.leftMargin, doc.bottomMargin + 1 * cm,
            doc.width, doc.height - 1 * cm,
            id="content_frame",
        )

        doc.addPageTemplates([
            PageTemplate(id="title_page", frames=[frame_title]),
            PageTemplate(
                id="content_page",
                frames=[frame_content],
                onPage=self._draw_header_footer,
            ),
        ])

        story = self._build_story()
        doc.build(story)

        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    # ------------------------------------------------------------------
    # Header / Footer
    # ------------------------------------------------------------------

    def _draw_header_footer(self, canvas, doc):
        """Draw running header and footer on content pages."""
        canvas.saveState()

        # Header line
        canvas.setStrokeColor(colors.HexColor("#1565c0"))
        canvas.setLineWidth(0.5)
        y_header = A4[1] - 1.5 * cm
        canvas.line(doc.leftMargin, y_header, A4[0] - doc.rightMargin, y_header)

        canvas.setFont(_BASE_FONT, 8)
        canvas.setFillColor(colors.HexColor("#78909c"))
        canvas.drawString(doc.leftMargin, A4[1] - 1.3 * cm,
                          f"АРИЗ-отчёт: {self.problem.title[:60]}")

        # Footer
        canvas.setFont(_BASE_FONT, 8)
        canvas.setFillColor(colors.HexColor("#9e9e9e"))
        footer_text = (
            f"Страница {doc.page}  |  ТРИЗ-Решатель  |  "
            f"{datetime.now().strftime('%d.%m.%Y')}"
        )
        canvas.drawCentredString(A4[0] / 2, 1 * cm, footer_text)

        y_footer = 1.3 * cm
        canvas.setStrokeColor(colors.HexColor("#e0e0e0"))
        canvas.line(doc.leftMargin, y_footer, A4[0] - doc.rightMargin, y_footer)

        canvas.restoreState()

    # ------------------------------------------------------------------
    # Story builder
    # ------------------------------------------------------------------

    def _build_story(self) -> list:
        """Build the full list of flowables."""
        story = []

        # Title page
        story.extend(self._build_title_page())
        story.append(NextPageTemplate("content_page"))
        story.append(PageBreak())

        # Content sections
        story.extend(self._build_problem_section())
        story.extend(self._build_steps_section())
        story.extend(self._build_contradictions_section())
        story.extend(self._build_ikr_section())
        story.extend(self._build_solutions_section())

        # Footer timestamp
        story.append(Spacer(1, 1 * cm))
        story.append(Paragraph(
            f"Сгенерировано ТРИЗ-Решателем {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            self.styles["SmallText"],
        ))

        return story

    # ------------------------------------------------------------------
    # Title page
    # ------------------------------------------------------------------

    def _build_title_page(self) -> list:
        elements = []
        elements.append(Spacer(1, 5 * cm))
        elements.append(Paragraph("ТРИЗ-Решатель", self.styles["TitlePage"]))
        elements.append(Spacer(1, 5 * mm))
        elements.append(Paragraph("Отчёт по сессии АРИЗ", self.styles["Subtitle"]))
        elements.append(Spacer(1, 3 * mm))

        mode_label = MODE_LABELS.get(self.session.mode, self.session.mode)
        elements.append(Paragraph(f"Режим: {mode_label}", self.styles["Subtitle"]))
        elements.append(Spacer(1, 2 * cm))

        elements.append(Paragraph(
            f"<b>Задача:</b> {self._esc(self.problem.title)}",
            ParagraphStyle(
                "TitleProblemCustom",
                parent=self.styles["BodyReport"],
                fontName=_BASE_FONT,
                fontSize=12,
                leading=16,
                alignment=TA_CENTER,
            ),
        ))
        elements.append(Spacer(1, 2.5 * cm))

        # Meta-information
        date_str = self.session.created_at.strftime("%d.%m.%Y %H:%M")
        info_lines = [f"Дата создания: {date_str}"]
        if self.session.completed_at:
            info_lines.append(
                f"Дата завершения: {self.session.completed_at.strftime('%d.%m.%Y %H:%M')}"
            )
        author_name = self.problem.user.get_full_name() or self.problem.user.username
        info_lines.append(f"Автор: {author_name}")

        info_style = ParagraphStyle(
            "TitleInfoCustom",
            parent=self.styles["BodyReport"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#78909c"),
        )
        for line in info_lines:
            elements.append(Paragraph(line, info_style))

        return elements

    # ------------------------------------------------------------------
    # Problem section
    # ------------------------------------------------------------------

    def _build_problem_section(self) -> list:
        elements = []
        elements.append(Paragraph("1. Описание задачи", self.styles["SectionHeading"]))
        elements.append(Paragraph(
            f"<b>Название:</b> {self._esc(self.problem.title)}",
            self.styles["BodyReport"],
        ))

        domain = DOMAIN_LABELS.get(self.problem.domain, self.problem.domain)
        elements.append(Paragraph(f"<b>Область:</b> {domain}", self.styles["BodyReport"]))

        if self.problem.original_description:
            elements.append(Paragraph("<b>Описание:</b>", self.styles["BodyReport"]))
            elements.append(Paragraph(
                self._esc(self.problem.original_description),
                self.styles["BodyReport"],
            ))

        elements.append(Spacer(1, 5 * mm))
        return elements

    # ------------------------------------------------------------------
    # Steps section
    # ------------------------------------------------------------------

    def _build_steps_section(self) -> list:
        elements = []
        steps = list(self.session.steps.filter(status="completed").order_by("created_at"))
        if not steps:
            return elements

        elements.append(Paragraph("2. Ход решения", self.styles["SectionHeading"]))

        if self.session.mode == "full":
            elements.extend(self._render_full_steps(steps))
        else:
            elements.extend(self._render_sequential_steps(steps))

        elements.append(Spacer(1, 5 * mm))
        return elements

    def _render_sequential_steps(self, steps) -> list:
        """Render steps sequentially (for express / autopilot mode)."""
        elements = []
        for step in steps:
            label = EXPRESS_LABELS.get(step.step_code, step.step_name)
            elements.extend(self._step_block(step, label))
        return elements

    def _render_full_steps(self, steps) -> list:
        """Render steps grouped by ARIZ parts."""
        elements = []
        current_part = None
        for step in steps:
            part_num = self._get_part_number(step.step_code)
            if part_num != current_part:
                current_part = part_num
                part_title = FULL_ARIZ_PARTS.get(part_num, f"Часть {part_num}")
                elements.append(Paragraph(part_title, self.styles["PartHeading"]))
            elements.extend(self._step_block(step, step.step_name))
        return elements

    def _step_block(self, step, label: str) -> list:
        """Render a single step block."""
        elements = []
        elements.append(Paragraph(
            f"Шаг {step.step_code}: {self._esc(label)}",
            self.styles["StepTitle"],
        ))

        if step.user_input:
            elements.append(Paragraph("<b>Ввод пользователя:</b>", self.styles["LabelStyle"]))
            elements.append(Paragraph(self._esc(step.user_input), self.styles["BodyReport"]))

        result_text = step.validated_result or step.llm_output
        if result_text:
            elements.append(Paragraph("<b>Результат:</b>", self.styles["LabelStyle"]))
            for paragraph in result_text.split("\n\n"):
                paragraph = paragraph.strip()
                if paragraph:
                    elements.append(Paragraph(
                        self._esc(paragraph).replace("\n", "<br/>"),
                        self.styles["BodyReport"],
                    ))

        if step.validation_notes:
            elements.append(Paragraph(
                f"<i>Примечание: {self._esc(step.validation_notes)}</i>",
                self.styles["SmallText"],
            ))

        elements.append(Spacer(1, 3 * mm))
        return elements

    # ------------------------------------------------------------------
    # Contradictions section
    # ------------------------------------------------------------------

    def _build_contradictions_section(self) -> list:
        elements = []
        contradictions = list(self.session.contradictions.all())
        if not contradictions:
            return elements

        elements.append(Paragraph("3. Противоречия", self.styles["SectionHeading"]))

        table_data = [[
            Paragraph("Тип", self.styles["TableHeaderStyle"]),
            Paragraph("Формулировка", self.styles["TableHeaderStyle"]),
            Paragraph("Свойство / Анти-свойство", self.styles["TableHeaderStyle"]),
        ]]

        for c in contradictions:
            type_label = CONTRADICTION_TYPE_LABELS.get(c.type, c.type)
            props = ""
            if c.property_s or c.anti_property_s:
                props = f"{c.property_s} / {c.anti_property_s}"
            elif c.quality_a or c.quality_b:
                props = f"{c.quality_a} / {c.quality_b}"

            table_data.append([
                Paragraph(type_label, self.styles["TableCellStyle"]),
                Paragraph(self._esc(c.formulation[:300]), self.styles["TableCellStyle"]),
                Paragraph(self._esc(props), self.styles["TableCellStyle"]),
            ])

        table = Table(table_data, colWidths=[3.5 * cm, 9 * cm, 4.5 * cm], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1565c0")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), _BOLD_FONT),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 5 * mm))
        return elements

    # ------------------------------------------------------------------
    # IKR section
    # ------------------------------------------------------------------

    def _build_ikr_section(self) -> list:
        elements = []
        ikrs = list(self.session.ikrs.all())
        if not ikrs:
            return elements

        elements.append(Paragraph(
            "4. Идеальный конечный результат (ИКР)",
            self.styles["SectionHeading"],
        ))

        for i, ikr in enumerate(ikrs, 1):
            elements.append(Paragraph(
                f"<b>ИКР-{i}:</b> {self._esc(ikr.formulation)}",
                self.styles["BodyReport"],
            ))
            if ikr.strengthened_formulation:
                elements.append(Paragraph(
                    f"<b>Усиленная формулировка:</b> {self._esc(ikr.strengthened_formulation)}",
                    self.styles["BodyReport"],
                ))
            if ikr.vpr_used:
                vpr_text = ", ".join(str(v) for v in ikr.vpr_used)
                elements.append(Paragraph(
                    f"<b>Использованные ВПР:</b> {self._esc(vpr_text)}",
                    self.styles["BodyReport"],
                ))
            elements.append(Spacer(1, 3 * mm))

        return elements

    # ------------------------------------------------------------------
    # Solutions section
    # ------------------------------------------------------------------

    def _build_solutions_section(self) -> list:
        elements = []
        solutions = list(self.session.solutions.all())
        if not solutions:
            return elements

        elements.append(Paragraph("5. Решения", self.styles["SectionHeading"]))

        for i, sol in enumerate(solutions, 1):
            method_label = METHOD_LABELS.get(sol.method_used, sol.method_used)

            elements.append(Paragraph(
                f"Решение {i}: {self._esc(sol.title)}",
                self.styles["PartHeading"],
            ))
            elements.append(Paragraph(
                f"<b>Метод:</b> {method_label}",
                self.styles["BodyReport"],
            ))
            elements.append(Paragraph(
                self._esc(sol.description),
                self.styles["BodyReport"],
            ))

            # Scores table
            novelty_style = self._score_style_name(sol.novelty_score)
            feasibility_style = self._score_style_name(sol.feasibility_score)

            score_data = [
                [
                    Paragraph("Показатель", self.styles["LabelStyle"]),
                    Paragraph("Оценка", self.styles["LabelStyle"]),
                    Paragraph("Уровень", self.styles["LabelStyle"]),
                ],
                [
                    Paragraph("Новизна", self.styles["BodyReport"]),
                    Paragraph(f"{sol.novelty_score}/10", self.styles[novelty_style]),
                    Paragraph(self._score_label(sol.novelty_score), self.styles["BodyReport"]),
                ],
                [
                    Paragraph("Реализуемость", self.styles["BodyReport"]),
                    Paragraph(f"{sol.feasibility_score}/10", self.styles[feasibility_style]),
                    Paragraph(self._score_label(sol.feasibility_score), self.styles["BodyReport"]),
                ],
            ]

            score_table = Table(score_data, colWidths=[5 * cm, 3 * cm, 5 * cm])
            score_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eceff1")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfd8dc")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(Spacer(1, 2 * mm))
            elements.append(score_table)
            elements.append(Spacer(1, 5 * mm))

        return elements

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_part_number(step_code: str) -> int:
        """Extract the part number from a step code (e.g. '2.3' -> 2)."""
        try:
            return int(step_code.split(".")[0])
        except (ValueError, IndexError):
            return 1

    @staticmethod
    def _esc(text: str) -> str:
        """Escape XML special characters for ReportLab Paragraph."""
        if not text:
            return ""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    @staticmethod
    def _score_style_name(score: int) -> str:
        """Return style name based on score value."""
        if score >= 7:
            return "ScoreHigh"
        if score >= 4:
            return "ScoreMedium"
        return "ScoreLow"

    @staticmethod
    def _score_label(score: int) -> str:
        """Return human-readable Russian label for a score."""
        if score >= 8:
            return "Отлично"
        if score >= 6:
            return "Хорошо"
        if score >= 4:
            return "Средне"
        if score >= 2:
            return "Ниже среднего"
        return "Низко"
