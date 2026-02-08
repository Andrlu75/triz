"""
Tests for report generation (PDF and DOCX).

Covers:
- PDF generation via PDFReportGenerator
- DOCX generation via DOCXReportGenerator
- API endpoints for downloading reports
- Access control (ownership check)
- Edge cases (empty sessions, sessions without solutions)
"""
import zipfile

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.ariz_engine.models import (
    ARIZSession,
    Contradiction,
    IKR,
    Solution,
    StepResult,
)
from apps.problems.models import Problem
from apps.reports.generators import DOCXReportGenerator, PDFReportGenerator
from apps.users.models import User


class ReportGeneratorMixin:
    """Shared setup for report generator tests."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
        )

        self.problem = Problem.objects.create(
            user=self.user,
            title="Test Problem: Improve Heat Exchange",
            original_description=(
                "A heat exchanger loses efficiency over time due to "
                "fouling on the inner surfaces. Need to find a way "
                "to maintain high heat transfer while preventing "
                "buildup of deposits."
            ),
            mode="express",
            domain="technical",
            status="completed",
        )

        self.session = ARIZSession.objects.create(
            problem=self.problem,
            mode="express",
            current_step="7",
            current_part=1,
            status="completed",
            completed_at=timezone.now(),
        )

        # Create step results
        steps_data = [
            ("1", "Формулировка задачи", "Задача теплообменника"),
            ("2", "Поверхностное противоречие", "Нужна гладкая поверхность и шероховатая для турбулентности"),
            ("3", "Углублённое противоречие", "Поверхность должна быть гладкой И шероховатой"),
            ("4", "Идеальный конечный результат", "Поверхность САМА предотвращает отложения"),
            ("5", "Обострённое противоречие", "Свойство поверхности должно присутствовать и отсутствовать"),
            ("6", "Углубление ОП", "Разделение во времени: поверхность меняет свойства"),
            ("7", "Решение", "Покрытие из сплава с памятью формы"),
        ]

        for code, name, result in steps_data:
            StepResult.objects.create(
                session=self.session,
                step_code=code,
                step_name=name,
                user_input=f"Ввод пользователя для шага {code}",
                llm_output=f"Анализ LLM для {name}",
                validated_result=result,
                validation_notes=f"Валидация пройдена для шага {code}",
                status="completed",
            )

        # Create contradiction
        Contradiction.objects.create(
            session=self.session,
            type="deepened",
            quality_a="Гладкость",
            quality_b="Шероховатость",
            property_s="Текстура поверхности",
            anti_property_s="Отсутствие текстуры",
            formulation="Поверхность должна быть гладкой И шероховатой одновременно",
        )

        # Create IKR
        IKR.objects.create(
            session=self.session,
            formulation="Поверхность САМА предотвращает загрязнение, сохраняя турбулентность",
            strengthened_formulation="Без дополнительных ресурсов поверхность динамически адаптируется",
            vpr_used=["материал поверхности", "температурный градиент"],
        )

        # Create solutions
        Solution.objects.create(
            session=self.session,
            method_used="principle",
            title="Покрытие из сплава с памятью формы",
            description=(
                "Нанести тонкое покрытие из сплава с памятью формы (SMA) на "
                "внутренние поверхности. При низкой температуре поверхность гладкая. "
                "При рабочей температуре SMA создаёт микро-турбулизаторы."
            ),
            novelty_score=8,
            feasibility_score=6,
        )
        Solution.objects.create(
            session=self.session,
            method_used="effect",
            title="Ультразвуковая самоочистка",
            description=(
                "Встроить пьезоэлектрические элементы в стенки теплообменника. "
                "Периодические ультразвуковые вибрации предотвращают отложения."
            ),
            novelty_score=7,
            feasibility_score=8,
        )


class TestPDFReportGenerator(ReportGeneratorMixin, TestCase):
    """Tests for PDF report generation."""

    def test_generate_returns_bytes(self):
        """PDF generator returns bytes."""
        generator = PDFReportGenerator(self.session)
        result = generator.generate()
        self.assertIsInstance(result, bytes)

    def test_generated_pdf_is_not_empty(self):
        """Generated PDF has non-zero content."""
        generator = PDFReportGenerator(self.session)
        result = generator.generate()
        self.assertGreater(len(result), 0)

    def test_generated_pdf_starts_with_pdf_header(self):
        """Generated PDF starts with %PDF header."""
        generator = PDFReportGenerator(self.session)
        result = generator.generate()
        self.assertTrue(result.startswith(b"%PDF"))

    def test_pdf_with_full_mode_session(self):
        """PDF generator works with full ARIZ mode (multi-part steps)."""
        self.session.mode = "full"
        self.session.save()

        StepResult.objects.create(
            session=self.session,
            step_code="1.1",
            step_name="Мини-задача",
            user_input="Ввод для полного режима",
            llm_output="Анализ полного режима",
            validated_result="Результат полного режима",
            status="completed",
        )

        generator = PDFReportGenerator(self.session)
        result = generator.generate()
        self.assertTrue(result.startswith(b"%PDF"))

    def test_pdf_with_empty_session(self):
        """PDF generator handles sessions with no steps gracefully."""
        empty_session = ARIZSession.objects.create(
            problem=self.problem,
            mode="express",
            status="completed",
            completed_at=timezone.now(),
        )
        generator = PDFReportGenerator(empty_session)
        result = generator.generate()
        self.assertTrue(result.startswith(b"%PDF"))

    def test_pdf_with_no_solutions(self):
        """PDF generator handles sessions without solutions."""
        self.session.solutions.all().delete()
        generator = PDFReportGenerator(self.session)
        result = generator.generate()
        self.assertGreater(len(result), 0)

    def test_pdf_with_no_contradictions(self):
        """PDF generator handles sessions without contradictions."""
        self.session.contradictions.all().delete()
        generator = PDFReportGenerator(self.session)
        result = generator.generate()
        self.assertTrue(result.startswith(b"%PDF"))

    def test_pdf_with_no_ikrs(self):
        """PDF generator handles sessions without IKRs."""
        self.session.ikrs.all().delete()
        generator = PDFReportGenerator(self.session)
        result = generator.generate()
        self.assertTrue(result.startswith(b"%PDF"))


class TestDOCXReportGenerator(ReportGeneratorMixin, TestCase):
    """Tests for DOCX report generation."""

    def test_generate_returns_bytes(self):
        """DOCX generator returns bytes."""
        generator = DOCXReportGenerator(self.session)
        result = generator.generate()
        self.assertIsInstance(result, bytes)

    def test_generated_docx_is_not_empty(self):
        """Generated DOCX has non-zero content."""
        generator = DOCXReportGenerator(self.session)
        result = generator.generate()
        self.assertGreater(len(result), 0)

    def test_generated_docx_is_valid_zip(self):
        """Generated DOCX is a valid ZIP file (DOCX format)."""
        import io

        generator = DOCXReportGenerator(self.session)
        result = generator.generate()
        self.assertTrue(zipfile.is_zipfile(io.BytesIO(result)))

    def test_docx_contains_document_xml(self):
        """Generated DOCX contains word/document.xml."""
        import io

        generator = DOCXReportGenerator(self.session)
        result = generator.generate()
        with zipfile.ZipFile(io.BytesIO(result)) as zf:
            self.assertIn("word/document.xml", zf.namelist())

    def test_docx_with_full_mode_session(self):
        """DOCX generator works with full ARIZ mode."""
        self.session.mode = "full"
        self.session.save()

        StepResult.objects.create(
            session=self.session,
            step_code="2.1",
            step_name="Анализ ресурсов",
            user_input="Ввод для полного режима",
            llm_output="Анализ полного режима",
            validated_result="Результат полного режима",
            status="completed",
        )

        generator = DOCXReportGenerator(self.session)
        result = generator.generate()
        self.assertGreater(len(result), 0)

    def test_docx_with_empty_session(self):
        """DOCX generator handles sessions with no steps."""
        empty_session = ARIZSession.objects.create(
            problem=self.problem,
            mode="express",
            status="completed",
            completed_at=timezone.now(),
        )
        generator = DOCXReportGenerator(empty_session)
        result = generator.generate()
        self.assertGreater(len(result), 0)

    def test_docx_with_no_solutions(self):
        """DOCX generator handles sessions without solutions."""
        self.session.solutions.all().delete()
        generator = DOCXReportGenerator(self.session)
        result = generator.generate()
        self.assertGreater(len(result), 0)

    def test_docx_with_no_contradictions(self):
        """DOCX generator handles sessions without contradictions."""
        self.session.contradictions.all().delete()
        generator = DOCXReportGenerator(self.session)
        result = generator.generate()
        self.assertGreater(len(result), 0)

    def test_docx_with_no_ikrs(self):
        """DOCX generator handles sessions without IKRs."""
        self.session.ikrs.all().delete()
        generator = DOCXReportGenerator(self.session)
        result = generator.generate()
        self.assertGreater(len(result), 0)


class TestReportAPIEndpoints(ReportGeneratorMixin, TestCase):
    """Tests for report download API endpoints."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_download_pdf_returns_200(self):
        """GET /api/v1/reports/{session_id}/download/pdf/ returns PDF."""
        response = self.client.get(
            f"/api/v1/reports/{self.session.pk}/download/pdf/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("Content-Disposition", response)
        self.assertIn("attachment", response["Content-Disposition"])

    def test_download_docx_returns_200(self):
        """GET /api/v1/reports/{session_id}/download/docx/ returns DOCX."""
        response = self.client.get(
            f"/api/v1/reports/{self.session.pk}/download/docx/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("wordprocessingml", response["Content-Type"])
        self.assertIn("attachment", response["Content-Disposition"])

    def test_download_nonexistent_session_returns_404(self):
        """Requesting report for non-existent session returns 404."""
        response = self.client.get(
            "/api/v1/reports/99999/download/pdf/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_download_other_users_session_returns_404(self):
        """Cannot download report for another user's session (returns 404)."""
        other_user = User.objects.create_user(
            username="otheruser",
            password="otherpass123",
            email="other@example.com",
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.get(
            f"/api/v1/reports/{self.session.pk}/download/pdf/"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_download_unauthenticated_returns_401(self):
        """Unauthenticated request returns 401."""
        self.client.force_authenticate(user=None)
        response = self.client.get(
            f"/api/v1/reports/{self.session.pk}/download/pdf/"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_download_incomplete_session_returns_400(self):
        """Downloading report for an incomplete session returns 400."""
        incomplete_session = ARIZSession.objects.create(
            problem=self.problem,
            mode="express",
            status="active",
        )
        response = self.client.get(
            f"/api/v1/reports/{incomplete_session.pk}/download/pdf/"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pdf_content_starts_with_pdf_header(self):
        """Downloaded PDF content starts with %PDF marker."""
        response = self.client.get(
            f"/api/v1/reports/{self.session.pk}/download/pdf/"
        )
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_docx_content_is_valid_zip(self):
        """Downloaded DOCX content is a valid ZIP file."""
        import io

        response = self.client.get(
            f"/api/v1/reports/{self.session.pk}/download/docx/"
        )
        self.assertTrue(zipfile.is_zipfile(io.BytesIO(response.content)))
