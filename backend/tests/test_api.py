"""
Tests for REST API endpoints — auth, problems, sessions.

All Celery tasks are mocked — no real LLM calls.
"""
from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.ariz_engine.models import ARIZSession, StepResult
from apps.problems.models import Problem
from apps.users.models import User

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def api_client():
    return APIClient()


@pytest.fixture()
def user():
    return User.objects.create_user(
        username="engineer",
        email="eng@example.com",
        password="testpass123",
    )


@pytest.fixture()
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture()
def problem(user):
    return Problem.objects.create(
        user=user,
        title="Overheating pipe",
        original_description="The pipe overheats during operation.",
        mode="express",
        domain="technical",
    )


@pytest.fixture()
def session(problem):
    return ARIZSession.objects.create(problem=problem, mode="express")


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------


class TestRegister:
    URL = "/api/v1/auth/register/"

    def test_register_success(self, api_client):
        resp = api_client.post(self.URL, {
            "username": "newuser",
            "email": "new@example.com",
            "password": "securepass1",
        })
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["username"] == "newuser"
        assert "password" not in resp.data
        assert User.objects.filter(username="newuser").exists()

    def test_register_short_password(self, api_client):
        resp = api_client.post(self.URL, {
            "username": "newuser",
            "password": "short",
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_username(self, api_client, user):
        resp = api_client.post(self.URL, {
            "username": user.username,
            "password": "testpass123",
        })
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


class TestLogin:
    URL = "/api/v1/auth/login/"

    def test_login_success(self, api_client, user):
        resp = api_client.post(self.URL, {
            "username": "engineer",
            "password": "testpass123",
        })
        assert resp.status_code == status.HTTP_200_OK
        assert "access" in resp.data
        assert "refresh" in resp.data

    def test_login_invalid(self, api_client):
        resp = api_client.post(self.URL, {
            "username": "nobody",
            "password": "wrong",
        })
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestRefresh:
    URL = "/api/v1/auth/refresh/"

    def test_refresh_token(self, api_client, user):
        login_resp = api_client.post("/api/v1/auth/login/", {
            "username": "engineer",
            "password": "testpass123",
        })
        refresh_token = login_resp.data["refresh"]

        resp = api_client.post(self.URL, {"refresh": refresh_token})
        assert resp.status_code == status.HTTP_200_OK
        assert "access" in resp.data


class TestMe:
    URL = "/api/v1/auth/me/"

    def test_me_authenticated(self, auth_client, user):
        resp = auth_client.get(self.URL)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["username"] == user.username

    def test_me_unauthenticated(self, api_client):
        resp = api_client.get(self.URL)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_me_update_locale(self, auth_client):
        resp = auth_client.patch(self.URL, {"locale": "en"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["locale"] == "en"


# ---------------------------------------------------------------------------
# Problem endpoints
# ---------------------------------------------------------------------------


class TestProblemList:
    URL = "/api/v1/problems/"

    def test_list_own_problems(self, auth_client, problem):
        resp = auth_client.get(self.URL)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 1
        assert resp.data["results"][0]["title"] == "Overheating pipe"

    def test_list_unauthenticated(self, api_client):
        resp = api_client.get(self.URL)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_excludes_other_users(self, auth_client, problem):
        other = User.objects.create_user(username="other", password="testpass123")
        Problem.objects.create(
            user=other,
            title="Other's problem",
            original_description="Not mine.",
        )
        resp = auth_client.get(self.URL)
        assert resp.data["count"] == 1


class TestProblemCreate:
    URL = "/api/v1/problems/"

    def test_create_problem(self, auth_client):
        resp = auth_client.post(self.URL, {
            "title": "New problem",
            "original_description": "Something is broken.",
            "mode": "express",
            "domain": "technical",
        })
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["title"] == "New problem"
        assert resp.data["status"] == "draft"

    def test_create_minimal(self, auth_client):
        resp = auth_client.post(self.URL, {
            "title": "Minimal",
            "original_description": "Just this.",
        })
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["mode"] == "express"
        assert resp.data["domain"] == "technical"


class TestProblemDetail:
    def test_retrieve(self, auth_client, problem):
        resp = auth_client.get(f"/api/v1/problems/{problem.pk}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["title"] == "Overheating pipe"

    def test_partial_update(self, auth_client, problem):
        resp = auth_client.patch(
            f"/api/v1/problems/{problem.pk}/",
            {"title": "Updated title"},
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["title"] == "Updated title"

    def test_delete(self, auth_client, problem):
        resp = auth_client.delete(f"/api/v1/problems/{problem.pk}/")
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not Problem.objects.filter(pk=problem.pk).exists()


# ---------------------------------------------------------------------------
# Session endpoints
# ---------------------------------------------------------------------------


class TestSessionStart:
    URL = "/api/v1/sessions/start/"

    def test_start_session(self, auth_client, problem):
        resp = auth_client.post(self.URL, {
            "problem_id": problem.pk,
            "mode": "express",
        })
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["mode"] == "express"
        assert resp.data["current_step"] == "1"
        assert resp.data["status"] == "active"

        problem.refresh_from_db()
        assert problem.status == "in_progress"

    def test_start_with_invalid_problem(self, auth_client):
        resp = auth_client.post(self.URL, {
            "problem_id": 99999,
            "mode": "express",
        })
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_start_other_users_problem(self, auth_client):
        other = User.objects.create_user(username="other", password="testpass123")
        other_problem = Problem.objects.create(
            user=other,
            title="Not mine",
            original_description="Other user's problem.",
        )
        resp = auth_client.post(self.URL, {
            "problem_id": other_problem.pk,
            "mode": "express",
        })
        assert resp.status_code == status.HTTP_404_NOT_FOUND


class TestSessionList:
    def test_list_sessions(self, auth_client, session):
        resp = auth_client.get("/api/v1/sessions/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) == 1

    def test_list_excludes_other_users(self, auth_client, session):
        other = User.objects.create_user(username="other", password="testpass123")
        other_problem = Problem.objects.create(
            user=other, title="Other", original_description="Other."
        )
        ARIZSession.objects.create(problem=other_problem, mode="express")

        resp = auth_client.get("/api/v1/sessions/")
        assert len(resp.data) == 1


class TestSessionRetrieve:
    def test_retrieve(self, auth_client, session):
        resp = auth_client.get(f"/api/v1/sessions/{session.pk}/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["id"] == session.pk


class TestSessionProgress:
    def test_progress(self, auth_client, problem):
        start_resp = auth_client.post("/api/v1/sessions/start/", {
            "problem_id": problem.pk,
            "mode": "express",
        })
        session_id = start_resp.data["id"]

        resp = auth_client.get(f"/api/v1/sessions/{session_id}/progress/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["current_step"] == "1"
        assert resp.data["total_steps"] == 7
        assert resp.data["percent"] == 0


class TestSessionCurrentStep:
    def test_current_step(self, auth_client, problem):
        start_resp = auth_client.post("/api/v1/sessions/start/", {
            "problem_id": problem.pk,
            "mode": "express",
        })
        session_id = start_resp.data["id"]

        resp = auth_client.get(f"/api/v1/sessions/{session_id}/current-step/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["step_code"] == "1"
        assert resp.data["status"] == "pending"


class TestSessionSubmit:
    @patch("apps.ariz_engine.engine.execute_ariz_step")
    def test_submit(self, mock_task, auth_client, problem):
        mock_task.delay.return_value = MagicMock(id="celery-task-456")

        start_resp = auth_client.post("/api/v1/sessions/start/", {
            "problem_id": problem.pk,
            "mode": "express",
        })
        session_id = start_resp.data["id"]

        resp = auth_client.post(
            f"/api/v1/sessions/{session_id}/submit/",
            {"user_input": "The pipe overheats badly."},
        )
        assert resp.status_code == status.HTTP_202_ACCEPTED
        assert resp.data["task_id"] == "celery-task-456"

    def test_submit_empty_input(self, auth_client, problem):
        start_resp = auth_client.post("/api/v1/sessions/start/", {
            "problem_id": problem.pk,
            "mode": "express",
        })
        session_id = start_resp.data["id"]

        resp = auth_client.post(
            f"/api/v1/sessions/{session_id}/submit/",
            {"user_input": ""},
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


class TestSessionAdvance:
    def test_advance(self, auth_client, problem):
        start_resp = auth_client.post("/api/v1/sessions/start/", {
            "problem_id": problem.pk,
            "mode": "express",
        })
        session_id = start_resp.data["id"]

        session = ARIZSession.objects.get(pk=session_id)
        StepResult.objects.filter(session=session, step_code="1").update(
            status="completed"
        )

        resp = auth_client.post(f"/api/v1/sessions/{session_id}/advance/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["step_code"] == "2"

    def test_advance_fails_if_not_completed(self, auth_client, problem):
        start_resp = auth_client.post("/api/v1/sessions/start/", {
            "problem_id": problem.pk,
            "mode": "express",
        })
        session_id = start_resp.data["id"]

        resp = auth_client.post(f"/api/v1/sessions/{session_id}/advance/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


class TestSessionBack:
    def test_back(self, auth_client, problem):
        start_resp = auth_client.post("/api/v1/sessions/start/", {
            "problem_id": problem.pk,
            "mode": "express",
        })
        session_id = start_resp.data["id"]

        session = ARIZSession.objects.get(pk=session_id)
        StepResult.objects.filter(session=session, step_code="1").update(
            status="completed"
        )

        auth_client.post(f"/api/v1/sessions/{session_id}/advance/")

        resp = auth_client.post(f"/api/v1/sessions/{session_id}/back/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["step_code"] == "1"

    def test_back_at_start(self, auth_client, problem):
        start_resp = auth_client.post("/api/v1/sessions/start/", {
            "problem_id": problem.pk,
            "mode": "express",
        })
        session_id = start_resp.data["id"]

        resp = auth_client.post(f"/api/v1/sessions/{session_id}/back/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


class TestSessionSummary:
    def test_summary(self, auth_client, problem):
        start_resp = auth_client.post("/api/v1/sessions/start/", {
            "problem_id": problem.pk,
            "mode": "express",
        })
        session_id = start_resp.data["id"]

        resp = auth_client.get(f"/api/v1/sessions/{session_id}/summary/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["mode"] == "express"
        assert "steps" in resp.data
        assert "contradictions" in resp.data
        assert "solutions" in resp.data


class TestTaskStatus:
    @patch("apps.ariz_engine.views.AsyncResult")
    def test_task_status_pending(self, mock_async, auth_client, session):
        mock_result = MagicMock()
        mock_result.status = "PENDING"
        mock_result.ready.return_value = False
        mock_async.return_value = mock_result

        resp = auth_client.get(
            f"/api/v1/sessions/{session.pk}/task/abc-def-123/"
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status"] == "PENDING"
        assert resp.data["ready"] is False

    @patch("apps.ariz_engine.views.AsyncResult")
    def test_task_status_success(self, mock_async, auth_client, session):
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.result = {"step_code": "1", "status": "completed"}
        mock_async.return_value = mock_result

        resp = auth_client.get(
            f"/api/v1/sessions/{session.pk}/task/abc-def-123/"
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["ready"] is True
        assert resp.data["result"]["status"] == "completed"


# ---------------------------------------------------------------------------
# E2E: Full Express cycle through API
# ---------------------------------------------------------------------------


class TestE2EExpressCycle:
    """
    E2E test: register → create problem → start session → submit/advance
    through all 7 express steps → session completed.
    """

    @patch("apps.ariz_engine.engine.execute_ariz_step")
    def test_full_express_cycle(self, mock_task, api_client):
        mock_task.delay.return_value = MagicMock(id="task-id")

        # 1. Register
        resp = api_client.post("/api/v1/auth/register/", {
            "username": "e2e_user",
            "email": "e2e@test.com",
            "password": "securepass1",
        })
        assert resp.status_code == status.HTTP_201_CREATED

        # 2. Login
        resp = api_client.post("/api/v1/auth/login/", {
            "username": "e2e_user",
            "password": "securepass1",
        })
        assert resp.status_code == status.HTTP_200_OK
        token = resp.data["access"]
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # 3. Create problem
        resp = api_client.post("/api/v1/problems/", {
            "title": "E2E Test Problem",
            "original_description": "Testing full cycle.",
            "mode": "express",
        })
        assert resp.status_code == status.HTTP_201_CREATED
        problem_id = resp.data["id"]

        # 4. Start session
        resp = api_client.post("/api/v1/sessions/start/", {
            "problem_id": problem_id,
            "mode": "express",
        })
        assert resp.status_code == status.HTTP_201_CREATED
        session_id = resp.data["id"]
        assert resp.data["current_step"] == "1"

        # 5. Walk through all 7 express steps
        for step_code in ["1", "2", "3", "4", "5", "6", "7"]:
            # Submit input
            resp = api_client.post(
                f"/api/v1/sessions/{session_id}/submit/",
                {"user_input": f"Input for step {step_code}"},
            )
            assert resp.status_code == status.HTTP_202_ACCEPTED

            # Simulate Celery completing the step
            session = ARIZSession.objects.get(pk=session_id)
            StepResult.objects.filter(
                session=session, step_code=step_code
            ).update(
                status="completed",
                llm_output=f"LLM output for step {step_code}",
            )

            # Check progress
            resp = api_client.get(f"/api/v1/sessions/{session_id}/progress/")
            assert resp.status_code == status.HTTP_200_OK

            # Advance (last step completes session)
            resp = api_client.post(f"/api/v1/sessions/{session_id}/advance/")
            assert resp.status_code == status.HTTP_200_OK

        # 6. Verify session completed
        session.refresh_from_db()
        assert session.status == "completed"
        assert session.completed_at is not None

        # 7. Check summary
        resp = api_client.get(f"/api/v1/sessions/{session_id}/summary/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status"] == "completed"
        assert len(resp.data["steps"]) == 7
