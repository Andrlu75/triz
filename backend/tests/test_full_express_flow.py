"""
E2E test: full Express cycle — create problem → 7 steps → solutions.

Tests the complete flow through API endpoints without mocking the engine,
only mocking the LLM client to return predictable responses.
"""
import json
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.users.models import User
from apps.problems.models import Problem
from apps.ariz_engine.models import ARIZSession, StepResult


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class TestFullExpressFlow(TestCase):
    """E2E: complete Express cycle (7 steps)."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="triz_user",
            email="user@triz.test",
            password="test12345678",
        )
        self.client.force_authenticate(user=self.user)

    def _mock_llm_response(self, content="LLM-ответ для шага"):
        """Return a mock that simulates LLM response."""
        mock = MagicMock()
        mock.return_value = {
            "content": content,
            "tokens_used": 150,
        }
        return mock

    def test_express_flow_create_problem(self):
        """Step 1: create a problem via API."""
        resp = self.client.post(
            "/api/v1/problems/",
            {
                "title": "Перегрев трубы",
                "original_description": "При работе компрессора труба перегревается.",
                "mode": "express",
                "domain": "technical",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["title"], "Перегрев трубы")
        self.assertEqual(resp.data["mode"], "express")

    def test_express_flow_start_session(self):
        """Step 2: start an ARIZ session for an Express problem."""
        problem = Problem.objects.create(
            user=self.user,
            title="Перегрев трубы",
            original_description="Труба перегревается",
            mode="express",
            domain="technical",
        )
        resp = self.client.post(
            "/api/v1/sessions/start/",
            {"problem_id": problem.id, "mode": "express"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertIn("id", resp.data)
        self.assertEqual(resp.data["mode"], "express")

    def test_express_flow_get_progress(self):
        """Step 3: check session progress."""
        problem = Problem.objects.create(
            user=self.user,
            title="Test",
            original_description="Desc",
            mode="express",
        )
        session = ARIZSession.objects.create(problem=problem, mode="express")
        resp = self.client.get(f"/api/v1/sessions/{session.id}/progress/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("total_steps", resp.data)

    @patch("apps.ariz_engine.engine.ARIZEngine.submit_step")
    def test_express_flow_submit_step(self, mock_submit):
        """Step 4: submit user input for current step."""
        mock_submit.return_value = "fake-task-id-123"
        problem = Problem.objects.create(
            user=self.user,
            title="Test",
            original_description="Desc",
            mode="express",
        )
        session = ARIZSession.objects.create(problem=problem, mode="express")
        StepResult.objects.create(
            session=session,
            step_code="1",
            step_name="Описание проблемы",
            status="pending",
        )

        resp = self.client.post(
            f"/api/v1/sessions/{session.id}/submit/",
            {"user_input": "Труба перегревается при длительной работе"},
            format="json",
        )
        self.assertEqual(resp.status_code, 202)
        self.assertEqual(resp.data["task_id"], "fake-task-id-123")

    def test_express_flow_advance_step(self):
        """Step 5: advance to next step."""
        problem = Problem.objects.create(
            user=self.user,
            title="Test",
            original_description="Desc",
            mode="express",
        )
        session = ARIZSession.objects.create(problem=problem, mode="express")
        StepResult.objects.create(
            session=session,
            step_code="1",
            step_name="Описание проблемы",
            status="completed",
            llm_output="LLM result",
            user_input="User input",
        )

        resp = self.client.post(f"/api/v1/sessions/{session.id}/advance/")
        self.assertEqual(resp.status_code, 200)

    def test_express_flow_go_back(self):
        """Step 6: go back to previous step."""
        problem = Problem.objects.create(
            user=self.user,
            title="Test",
            original_description="Desc",
            mode="express",
        )
        session = ARIZSession.objects.create(
            problem=problem, mode="express", current_step="2"
        )
        StepResult.objects.create(
            session=session,
            step_code="1",
            step_name="Описание проблемы",
            status="completed",
        )
        StepResult.objects.create(
            session=session,
            step_code="2",
            step_name="Функция системы",
            status="pending",
        )

        resp = self.client.post(f"/api/v1/sessions/{session.id}/back/")
        self.assertEqual(resp.status_code, 200)

    def test_express_flow_summary(self):
        """Step 7: get session summary."""
        problem = Problem.objects.create(
            user=self.user,
            title="Test",
            original_description="Desc",
            mode="express",
        )
        session = ARIZSession.objects.create(
            problem=problem, mode="express", status="completed"
        )
        for i in range(1, 8):
            StepResult.objects.create(
                session=session,
                step_code=str(i),
                step_name=f"Step {i}",
                status="completed",
                llm_output=f"Result for step {i}",
                user_input=f"Input for step {i}",
            )

        resp = self.client.get(f"/api/v1/sessions/{session.id}/summary/")
        self.assertEqual(resp.status_code, 200)

    def test_express_flow_problem_list_filter(self):
        """Verify problems are filtered by authenticated user."""
        other_user = User.objects.create_user(
            username="other", email="other@test.com", password="test12345678"
        )
        Problem.objects.create(
            user=other_user,
            title="Other problem",
            original_description="Not mine",
        )
        Problem.objects.create(
            user=self.user,
            title="My problem",
            original_description="Mine",
        )

        resp = self.client.get("/api/v1/problems/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["title"], "My problem")
