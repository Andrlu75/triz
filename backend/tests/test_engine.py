"""
Tests for ARIZEngine — start, advance, go_back, progress, summary.

All Celery tasks are mocked — no real LLM calls.
"""
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from apps.ariz_engine.engine import ARIZEngine
from apps.ariz_engine.models import (
    ARIZSession,
    Contradiction,
    IKR,
    Solution,
    StepResult,
)
from apps.ariz_engine.steps.registry import (
    EXPRESS_STEPS,
    FULL_STEPS,
    get_next_step,
    get_previous_step,
    get_step_def,
    get_steps_for_mode,
)
from apps.problems.models import Problem
from apps.users.models import User

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def user():
    return User.objects.create_user(username="engineer", password="testpass")


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


@pytest.fixture()
def engine(session):
    return ARIZEngine(session)


# ---------------------------------------------------------------------------
# Step registry tests
# ---------------------------------------------------------------------------


class TestStepRegistry:
    def test_express_has_7_steps(self):
        assert len(EXPRESS_STEPS) == 7

    def test_full_has_24_steps(self):
        assert len(FULL_STEPS) == 24

    def test_express_step_codes_sequential(self):
        codes = [s.code for s in EXPRESS_STEPS]
        assert codes == ["1", "2", "3", "4", "5", "6", "7"]

    def test_full_step_codes_start_with_part(self):
        for step in FULL_STEPS:
            part = step.code.split(".")[0]
            assert part in ("1", "2", "3", "4")

    def test_get_steps_for_mode(self):
        assert get_steps_for_mode("express") == EXPRESS_STEPS
        assert get_steps_for_mode("full") == FULL_STEPS
        assert get_steps_for_mode("autopilot") == EXPRESS_STEPS

    def test_get_step_def(self):
        step = get_step_def("express", "1")
        assert step is not None
        assert step.name == "Формулировка задачи"

    def test_get_step_def_full(self):
        step = get_step_def("full", "1.1")
        assert step is not None
        assert step.name == "Мини-задача"

    def test_get_next_step(self):
        nxt = get_next_step("express", "1")
        assert nxt is not None
        assert nxt.code == "2"

    def test_get_next_step_last(self):
        nxt = get_next_step("express", "7")
        assert nxt is None

    def test_get_previous_step(self):
        prev = get_previous_step("express", "3")
        assert prev is not None
        assert prev.code == "2"

    def test_get_previous_step_first(self):
        prev = get_previous_step("express", "1")
        assert prev is None

    def test_all_steps_have_prompts(self):
        for step in EXPRESS_STEPS:
            assert step.prompt.endswith(".j2")

    def test_step_1_has_falseness_validator(self):
        step = get_step_def("express", "1")
        assert "falseness_check" in step.validators


# ---------------------------------------------------------------------------
# ARIZEngine tests
# ---------------------------------------------------------------------------


class TestARIZEngineStart:
    def test_start_session(self, engine, session):
        step_result = engine.start_session()
        assert step_result.step_code == "1"
        assert step_result.status == "pending"
        session.refresh_from_db()
        assert session.current_step == "1"
        assert session.status == "active"

    def test_start_creates_step_result(self, engine, session):
        engine.start_session()
        assert StepResult.objects.filter(session=session, step_code="1").exists()


class TestARIZEngineSubmit:
    @patch("apps.ariz_engine.engine.execute_ariz_step")
    def test_submit_step(self, mock_task, engine, session):
        engine.start_session()
        mock_task.delay.return_value = MagicMock(id="celery-task-123")

        task_id = engine.submit_step("The pipe overheats badly.")

        assert task_id == "celery-task-123"
        mock_task.delay.assert_called_once()
        call_kwargs = mock_task.delay.call_args[1]
        assert call_kwargs["session_id"] == session.pk
        assert call_kwargs["step_code"] == "1"
        assert call_kwargs["user_input"] == "The pipe overheats badly."
        assert "falseness_check" in call_kwargs["validators"]


class TestARIZEngineAdvance:
    def test_advance_to_next(self, engine, session):
        engine.start_session()
        StepResult.objects.filter(session=session, step_code="1").update(status="completed")

        next_step = engine.advance_to_next()
        assert next_step is not None
        assert next_step.step_code == "2"
        session.refresh_from_db()
        assert session.current_step == "2"

    def test_advance_at_end_completes_session(self, engine, session):
        engine.start_session()
        session.current_step = "7"
        session.save()
        StepResult.objects.create(session=session, step_code="7", step_name="S7", status="completed")

        result = engine.advance_to_next()
        assert result is None
        session.refresh_from_db()
        assert session.status == "completed"
        assert session.completed_at is not None

    def test_advance_fails_if_not_completed(self, engine, session):
        engine.start_session()
        with pytest.raises(ValueError, match="not completed"):
            engine.advance_to_next()


class TestARIZEngineGoBack:
    def test_go_back(self, engine, session):
        engine.start_session()
        session.current_step = "3"
        session.save()
        StepResult.objects.create(session=session, step_code="2", step_name="S2", status="completed")

        prev = engine.go_back()
        assert prev is not None
        assert prev.step_code == "2"
        session.refresh_from_db()
        assert session.current_step == "2"

    def test_go_back_at_start(self, engine, session):
        engine.start_session()
        result = engine.go_back()
        assert result is None


class TestARIZEngineProgress:
    def test_initial_progress(self, engine, session):
        engine.start_session()
        progress = engine.get_progress()
        assert progress["current_step"] == "1"
        assert progress["total_steps"] == 7
        assert progress["completed_count"] == 0
        assert progress["percent"] == 0

    def test_progress_after_steps(self, engine, session):
        engine.start_session()
        for code in ["1", "2", "3"]:
            StepResult.objects.create(
                session=session, step_code=code, step_name=f"S{code}", status="completed"
            )
        session.current_step = "4"
        session.save()

        progress = engine.get_progress()
        assert progress["completed_count"] == 3
        assert progress["percent"] == 43  # 3/7 ≈ 42.8


class TestARIZEngineSummary:
    def test_session_summary(self, engine, session):
        engine.start_session()
        StepResult.objects.create(
            session=session, step_code="1", step_name="Problem formulation",
            user_input="Input", llm_output="Output", validated_result="Validated",
            status="completed",
        )
        Contradiction.objects.create(
            session=session, type="surface", formulation="If A then not B",
        )
        IKR.objects.create(session=session, formulation="Element does X by itself")
        Solution.objects.create(
            session=session, method_used="principle", title="Layered structure",
            description="Use layers", novelty_score=8, feasibility_score=7,
        )

        summary = engine.get_session_summary()
        assert summary["mode"] == "express"
        assert len(summary["steps"]) == 2  # start_session created step + our step
        assert len(summary["contradictions"]) == 1
        assert len(summary["ikrs"]) == 1
        assert len(summary["solutions"]) == 1
        assert summary["problem"]["title"] == "Overheating pipe"
