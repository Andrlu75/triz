"""
E2E test: full ARIZ-2010 cycle — create problem → 24 steps across 4 parts.

Tests the complete Full ARIZ flow through API endpoints.
"""
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.users.models import User
from apps.problems.models import Problem
from apps.ariz_engine.models import ARIZSession, StepResult


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class TestFullARIZFlow(TestCase):
    """E2E: Full ARIZ-2010 cycle (24 steps, 4 parts)."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="ariz_user",
            email="ariz@triz.test",
            password="test12345678",
            plan="business",  # Full mode requires Business plan
        )
        self.client.force_authenticate(user=self.user)

    def test_create_full_problem(self):
        """Create a problem with Full ARIZ mode."""
        resp = self.client.post(
            "/api/v1/problems/",
            {
                "title": "Повышение прочности детали",
                "original_description": "Деталь должна быть лёгкой и прочной одновременно.",
                "mode": "full",
                "domain": "technical",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["mode"], "full")

    def test_start_full_session(self):
        """Start a Full ARIZ session."""
        problem = Problem.objects.create(
            user=self.user,
            title="Тест полного АРИЗ",
            original_description="Описание задачи для полного АРИЗ",
            mode="full",
            domain="technical",
        )
        resp = self.client.post(
            "/api/v1/sessions/start/",
            {"problem_id": problem.id, "mode": "full"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["mode"], "full")

    def test_full_session_progress_24_steps(self):
        """Verify Full mode reports 24 total steps."""
        problem = Problem.objects.create(
            user=self.user,
            title="Тест прогресса",
            original_description="Desc",
            mode="full",
        )
        session = ARIZSession.objects.create(
            problem=problem, mode="full", current_step="1.1"
        )
        resp = self.client.get(f"/api/v1/sessions/{session.id}/progress/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["total_steps"], 24)

    def test_full_session_part_tracking(self):
        """Verify session tracks current part."""
        problem = Problem.objects.create(
            user=self.user,
            title="Тест частей",
            original_description="Desc",
            mode="full",
        )
        session = ARIZSession.objects.create(
            problem=problem, mode="full", current_step="1.1", current_part=1
        )
        self.assertEqual(session.current_part, 1)

        session.current_step = "2.1"
        session.current_part = 2
        session.save()
        session.refresh_from_db()
        self.assertEqual(session.current_part, 2)

    @patch("apps.ariz_engine.engine.ARIZEngine.submit_step")
    def test_full_submit_step_1_1(self, mock_submit):
        """Submit user input for step 1.1 (mini-task)."""
        mock_submit.return_value = "task-uuid-123"
        problem = Problem.objects.create(
            user=self.user,
            title="Тест сабмита",
            original_description="Desc",
            mode="full",
        )
        session = ARIZSession.objects.create(
            problem=problem, mode="full", current_step="1.1"
        )
        StepResult.objects.create(
            session=session,
            step_code="1.1",
            step_name="Мини-задача",
            status="pending",
        )

        resp = self.client.post(
            f"/api/v1/sessions/{session.id}/submit/",
            {"user_input": "Деталь должна быть лёгкой для транспортировки"},
            format="json",
        )
        self.assertEqual(resp.status_code, 202)
        self.assertIn("task_id", resp.data)

    def test_full_session_all_steps_completed(self):
        """Verify summary works when all 24 steps are completed."""
        problem = Problem.objects.create(
            user=self.user,
            title="Полный цикл",
            original_description="Desc",
            mode="full",
        )
        session = ARIZSession.objects.create(
            problem=problem, mode="full", status="completed"
        )

        # Create all 24 step results
        full_steps = [
            "1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7",
            "2.1", "2.2", "2.3",
            "3.1", "3.2", "3.3", "3.4", "3.5", "3.6",
            "4.1", "4.2", "4.3", "4.4", "4.5", "4.6", "4.7", "4.8",
        ]
        for code in full_steps:
            StepResult.objects.create(
                session=session,
                step_code=code,
                step_name=f"Step {code}",
                status="completed",
                llm_output=f"Result for {code}",
                user_input=f"Input for {code}",
            )

        resp = self.client.get(f"/api/v1/sessions/{session.id}/summary/")
        self.assertEqual(resp.status_code, 200)

    def test_full_advance_through_parts(self):
        """Test advancing from Part 1 to Part 2."""
        problem = Problem.objects.create(
            user=self.user,
            title="Тест перехода",
            original_description="Desc",
            mode="full",
        )
        session = ARIZSession.objects.create(
            problem=problem, mode="full", current_step="1.7"
        )
        # Complete step 1.7
        StepResult.objects.create(
            session=session,
            step_code="1.7",
            step_name="Применение стандартов",
            status="completed",
            llm_output="Standards checked",
            user_input="Confirmed",
        )

        resp = self.client.post(f"/api/v1/sessions/{session.id}/advance/")
        self.assertEqual(resp.status_code, 200)
        session.refresh_from_db()
        self.assertEqual(session.current_step, "2.1")
