"""
Tests for Celery tasks (apps.llm_service.tasks).

All tests mock the OpenAI client and PromptManager — no real API calls.
"""
import pytest
from unittest.mock import MagicMock, patch

from apps.ariz_engine.models import ARIZSession, StepResult
from apps.llm_service.client import LLMResponse
from apps.llm_service.tasks import (
    _build_context,
    _parse_validation_response,
    _run_validation,
    _update_context_snapshot,
    execute_ariz_step,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def problem(db):
    """Create a test Problem instance."""
    from apps.problems.models import Problem
    from apps.users.models import User

    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )
    return Problem.objects.create(
        user=user,
        title="Test Bridge Problem",
        original_description="The bridge is too weak for heavy trucks.",
        mode="express",
        domain="technical",
        status="in_progress",
    )


@pytest.fixture
def session(db, problem):
    """Create a test ARIZSession."""
    return ARIZSession.objects.create(
        problem=problem,
        mode="express",
        current_step="1",
        status="active",
    )


@pytest.fixture
def completed_step(db, session):
    """Create a completed StepResult for the session."""
    return StepResult.objects.create(
        session=session,
        step_code="1",
        step_name="Step 1: Problem Formulation",
        user_input="The bridge can't handle heavy trucks.",
        llm_output="Analysis: The main issue is...",
        validated_result="Analysis: The main issue is structural weakness.",
        status="completed",
    )


def _make_llm_response(content="LLM analysis result", **kwargs):
    """Create a mock LLMResponse."""
    defaults = {
        "content": content,
        "model": "gpt-4o",
        "input_tokens": 200,
        "output_tokens": 100,
        "total_tokens": 300,
        "cost_usd": 0.0015,
        "finish_reason": "stop",
        "latency_ms": 1500.0,
    }
    defaults.update(kwargs)
    return LLMResponse(**defaults)


# ---------------------------------------------------------------------------
# _build_context tests
# ---------------------------------------------------------------------------


class TestBuildContext:
    """Tests for the context builder."""

    @pytest.mark.django_db
    def test_basic_context_fields(self, session):
        """Context should include problem and session data."""
        context = _build_context(session, "User input text")

        assert context["problem_title"] == "Test Bridge Problem"
        assert "bridge" in context["problem_description"].lower()
        assert context["mode"] == "express"
        assert context["user_input"] == "User input text"
        assert context["current_step"] == "1"

    @pytest.mark.django_db
    def test_context_with_previous_steps(self, session, completed_step):
        """Context should include formatted previous step results."""
        context = _build_context(session, "New input")

        assert "previous_results" in context
        assert "Step 1" in context["previous_results"]
        assert "structural weakness" in context["previous_results"]
        assert len(context["previous_steps"]) == 1

    @pytest.mark.django_db
    def test_context_without_previous_steps(self, session):
        """Context with no previous steps should have empty previous results."""
        context = _build_context(session, "First input")

        assert context["previous_results"] == ""
        assert context["previous_steps"] == []

    @pytest.mark.django_db
    def test_context_snapshot_included(self, session):
        """Context should include the session's context_snapshot."""
        session.context_snapshot = {"steps": {"1": "result"}, "key": "value"}
        session.save()

        context = _build_context(session, "Input")
        assert context["context_snapshot"]["key"] == "value"


# ---------------------------------------------------------------------------
# _parse_validation_response tests
# ---------------------------------------------------------------------------


class TestParseValidationResponse:
    """Tests for the JSON validation response parser."""

    def test_valid_json(self):
        """Should parse a clean JSON response."""
        content = '{"valid": true, "issues": [], "suggestions": ["Good work"]}'
        result = _parse_validation_response(content)
        assert result["valid"] is True

    def test_json_in_code_block(self):
        """Should extract JSON from markdown code blocks."""
        content = '```json\n{"valid": false, "issues": ["Problem found"]}\n```'
        result = _parse_validation_response(content)
        assert result["valid"] is False
        assert "Problem found" in result.get("issues", [])

    def test_invalid_json_returns_default(self):
        """Should return valid=True for unparseable responses."""
        content = "This is not JSON at all."
        result = _parse_validation_response(content)
        assert result["valid"] is True

    def test_empty_content(self):
        """Should handle empty content gracefully."""
        result = _parse_validation_response("")
        assert result["valid"] is True

    def test_partial_json(self):
        """Should handle truncated JSON gracefully."""
        content = '{"valid": true, "issues": ['
        result = _parse_validation_response(content)
        assert result["valid"] is True  # fallback


# ---------------------------------------------------------------------------
# _update_context_snapshot tests
# ---------------------------------------------------------------------------


class TestUpdateContextSnapshot:
    """Tests for session context snapshot updates."""

    @pytest.mark.django_db
    def test_adds_step_to_snapshot(self, session):
        """Should add step result to the snapshot."""
        _update_context_snapshot(session, "1", "user input", "Step 1 result")

        session.refresh_from_db()
        assert "steps" in session.context_snapshot
        assert "1" in session.context_snapshot["steps"]
        assert session.context_snapshot["steps"]["1"]["result"] == "Step 1 result"

    @pytest.mark.django_db
    def test_tracks_last_completed_step(self, session):
        """Should track which step was last completed."""
        _update_context_snapshot(session, "1", "input1", "Result 1")
        _update_context_snapshot(session, "2", "input2", "Result 2")

        session.refresh_from_db()
        assert session.context_snapshot["last_completed_step"] == "2"

    @pytest.mark.django_db
    def test_preserves_existing_data(self, session):
        """Should not overwrite data from previous steps."""
        _update_context_snapshot(session, "1", "input1", "Result 1")
        _update_context_snapshot(session, "2", "input2", "Result 2")

        session.refresh_from_db()
        assert "1" in session.context_snapshot["steps"]
        assert "2" in session.context_snapshot["steps"]


# ---------------------------------------------------------------------------
# _run_validation tests
# ---------------------------------------------------------------------------


class TestRunValidation:
    """Tests for the validation runner."""

    def test_no_validators_returns_output(self):
        """Without validators, should return the original output as-is."""
        client = MagicMock()
        pm = MagicMock()

        validated, notes = _run_validation(
            client=client,
            prompt_manager=pm,
            validators=[],
            llm_output="Original output",
            context={},
        )

        assert validated == "Original output"
        assert notes == ""
        client.send_validation.assert_not_called()

    def test_valid_output_returned(self):
        """Valid output should be returned unchanged."""
        client = MagicMock()
        client.send_validation.return_value = _make_llm_response(
            content='{"valid": true, "issues": [], "suggestions": ["Clear"]}'
        )
        pm = MagicMock()
        pm.render_validation_prompt.return_value = "Validate this"

        validated, notes = _run_validation(
            client=client,
            prompt_manager=pm,
            validators=["falseness_check"],
            llm_output="Good output",
            context={},
        )

        assert validated == "Good output"

    def test_invalid_output_uses_corrected(self):
        """Invalid output should use corrected_output if available."""
        client = MagicMock()
        client.send_validation.return_value = _make_llm_response(
            content='{"valid": false, "issues": ["Wrong format"], "corrected_output": "Fixed output"}'
        )
        pm = MagicMock()
        pm.render_validation_prompt.return_value = "Validate"

        validated, notes = _run_validation(
            client=client,
            prompt_manager=pm,
            validators=["terms_check"],
            llm_output="Bad output",
            context={},
        )

        assert validated == "Fixed output"
        assert "Wrong format" in notes

    def test_validation_error_returns_original(self):
        """On validation error, should return original output."""
        client = MagicMock()
        client.send_validation.side_effect = Exception("API error")
        pm = MagicMock()
        pm.render_validation_prompt.return_value = "Validate"

        validated, notes = _run_validation(
            client=client,
            prompt_manager=pm,
            validators=["falseness_check"],
            llm_output="Original output",
            context={},
        )

        assert validated == "Original output"
        assert "error" in notes.lower()


# ---------------------------------------------------------------------------
# execute_ariz_step tests
# ---------------------------------------------------------------------------


class TestExecuteARIZStep:
    """Tests for the main Celery task."""

    @pytest.mark.django_db
    @patch("apps.llm_service.tasks.OpenAIClient")
    @patch("apps.llm_service.tasks.PromptManager")
    def test_successful_execution(self, MockPM, MockClient, session):
        """Task should complete successfully and create a StepResult."""
        # Setup mocks
        mock_client = MockClient.return_value
        mock_client.send_message.return_value = _make_llm_response(
            content="LLM analysis of the bridge problem."
        )

        mock_pm = MockPM.return_value
        mock_pm.render_system_prompt.return_value = "System prompt"
        mock_pm.render_step_prompt.return_value = "Step prompt"

        result = execute_ariz_step(
            session_id=session.pk,
            step_code="1",
            user_input="The bridge is failing.",
        )

        assert result["status"] == "completed"
        assert result["step_code"] == "1"
        assert result["session_id"] == session.pk

        # Verify StepResult was created
        step = StepResult.objects.get(session=session, step_code="1")
        assert step.status == "completed"
        assert "LLM analysis" in step.llm_output
        assert step.user_input == "The bridge is failing."

    @pytest.mark.django_db
    @patch("apps.llm_service.tasks.OpenAIClient")
    @patch("apps.llm_service.tasks.PromptManager")
    def test_context_snapshot_updated(self, MockPM, MockClient, session):
        """Task should update the session's context_snapshot."""
        mock_client = MockClient.return_value
        mock_client.send_message.return_value = _make_llm_response(content="Result text")

        mock_pm = MockPM.return_value
        mock_pm.render_system_prompt.return_value = "System"
        mock_pm.render_step_prompt.return_value = "Step"

        execute_ariz_step(
            session_id=session.pk,
            step_code="2",
            user_input="Test input",
        )

        session.refresh_from_db()
        assert "steps" in session.context_snapshot
        assert "2" in session.context_snapshot["steps"]
        assert session.context_snapshot["last_completed_step"] == "2"

    @pytest.mark.django_db
    def test_nonexistent_session(self):
        """Task should raise when session does not exist."""
        with pytest.raises(ARIZSession.DoesNotExist):
            execute_ariz_step(
                session_id=999999,
                step_code="1",
                user_input="Test",
            )

    @pytest.mark.django_db
    @patch("apps.llm_service.tasks.OpenAIClient")
    @patch("apps.llm_service.tasks.PromptManager")
    def test_existing_step_result_updated(self, MockPM, MockClient, session):
        """Task should update existing StepResult instead of creating new one."""
        # Pre-create a step result
        existing = StepResult.objects.create(
            session=session,
            step_code="1",
            step_name="Step 1",
            user_input="Old input",
            status="pending",
        )

        mock_client = MockClient.return_value
        mock_client.send_message.return_value = _make_llm_response(content="New analysis")

        mock_pm = MockPM.return_value
        mock_pm.render_system_prompt.return_value = "System"
        mock_pm.render_step_prompt.return_value = "Step"

        execute_ariz_step(
            session_id=session.pk,
            step_code="1",
            user_input="New input",
        )

        existing.refresh_from_db()
        assert existing.user_input == "New input"
        assert existing.status == "completed"
        assert "New analysis" in existing.llm_output

    @pytest.mark.django_db
    @patch("apps.llm_service.tasks.OpenAIClient")
    @patch("apps.llm_service.tasks.PromptManager")
    def test_with_validators(self, MockPM, MockClient, session):
        """Task should run validation when validators are provided."""
        mock_client = MockClient.return_value
        mock_client.send_message.return_value = _make_llm_response(content="Step output")
        mock_client.send_validation.return_value = _make_llm_response(
            content='{"valid": true, "issues": [], "suggestions": ["Looks good"]}'
        )

        mock_pm = MockPM.return_value
        mock_pm.render_system_prompt.return_value = "System"
        mock_pm.render_step_prompt.return_value = "Step"
        mock_pm.render_validation_prompt.return_value = "Validate this"

        result = execute_ariz_step(
            session_id=session.pk,
            step_code="1",
            user_input="Test",
            validators=["falseness_check"],
        )

        assert result["status"] == "completed"
        mock_client.send_validation.assert_called_once()

    @pytest.mark.django_db
    @patch("apps.llm_service.tasks.OpenAIClient")
    @patch("apps.llm_service.tasks.PromptManager")
    def test_llm_error_marks_step_failed(self, MockPM, MockClient, session):
        """LLM error should mark the step as failed."""
        mock_client = MockClient.return_value
        mock_client.send_message.side_effect = Exception("OpenAI API error")

        mock_pm = MockPM.return_value
        mock_pm.render_system_prompt.return_value = "System"
        mock_pm.render_step_prompt.return_value = "Step"

        # The task should raise (for Celery retry) but step should be marked failed
        with pytest.raises(Exception):
            execute_ariz_step(
                session_id=session.pk,
                step_code="1",
                user_input="Test",
            )

        step = StepResult.objects.get(session=session, step_code="1")
        assert step.status == "failed"
        assert "Error" in step.validation_notes

    @pytest.mark.django_db
    @patch("apps.llm_service.tasks.OpenAIClient")
    @patch("apps.llm_service.tasks.PromptManager")
    def test_prompt_manager_called_correctly(self, MockPM, MockClient, session):
        """Task should call PromptManager with correct arguments."""
        mock_client = MockClient.return_value
        mock_client.send_message.return_value = _make_llm_response()

        mock_pm = MockPM.return_value
        mock_pm.render_system_prompt.return_value = "System prompt text"
        mock_pm.render_step_prompt.return_value = "Step prompt text"

        execute_ariz_step(
            session_id=session.pk,
            step_code="3",
            user_input="Analyze contradictions",
        )

        mock_pm.render_system_prompt.assert_called_once_with(mode="express")
        mock_pm.render_step_prompt.assert_called_once()
        call_kwargs = mock_pm.render_step_prompt.call_args
        assert call_kwargs.kwargs["step_code"] == "3"
        assert call_kwargs.kwargs["mode"] == "express"

    @pytest.mark.django_db
    @patch("apps.llm_service.tasks.OpenAIClient")
    @patch("apps.llm_service.tasks.PromptManager")
    def test_step_name_from_argument(self, MockPM, MockClient, session):
        """Task should use the step_name argument if provided."""
        mock_client = MockClient.return_value
        mock_client.send_message.return_value = _make_llm_response()

        mock_pm = MockPM.return_value
        mock_pm.render_system_prompt.return_value = "System"
        mock_pm.render_step_prompt.return_value = "Step"

        execute_ariz_step(
            session_id=session.pk,
            step_code="1",
            user_input="Test",
            step_name="Formulation of the problem",
        )

        step = StepResult.objects.get(session=session, step_code="1")
        assert step.step_name == "Formulation of the problem"

    @pytest.mark.django_db
    @patch("apps.llm_service.tasks.OpenAIClient")
    @patch("apps.llm_service.tasks.PromptManager")
    def test_cost_tracking(self, MockPM, MockClient, session):
        """Task result should include cost information."""
        mock_client = MockClient.return_value
        mock_client.send_message.return_value = _make_llm_response(
            input_tokens=500, output_tokens=250, cost_usd=0.00375
        )

        mock_pm = MockPM.return_value
        mock_pm.render_system_prompt.return_value = "System"
        mock_pm.render_step_prompt.return_value = "Step"

        result = execute_ariz_step(
            session_id=session.pk,
            step_code="1",
            user_input="Test",
        )

        assert result["input_tokens"] == 500
        assert result["output_tokens"] == 250
        assert result["cost_usd"] == 0.00375
