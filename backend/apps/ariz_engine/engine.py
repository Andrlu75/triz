"""
ARIZEngine — orchestrator for ARIZ sessions.

Manages the state machine of steps, dispatches LLM tasks via Celery,
and tracks progress through the ARIZ methodology.
"""
import logging

from django.utils import timezone

from apps.ariz_engine.models import ARIZSession, Contradiction, IKR, Solution, StepResult
from apps.ariz_engine.steps.registry import (
    get_next_step,
    get_previous_step,
    get_step_def,
    get_steps_for_mode,
)
from apps.llm_service.tasks import execute_ariz_step

logger = logging.getLogger(__name__)


class ARIZEngine:
    """
    Orchestrates an ARIZ session. Manages the step state machine.

    Usage::

        engine = ARIZEngine(session)
        first_step = engine.start_session()
        task_id = engine.submit_step("User describes the problem...")
        # ... poll task status ...
        next_step = engine.advance_to_next()
    """

    def __init__(self, session: ARIZSession):
        self.session = session
        self.mode = session.mode
        self.steps = get_steps_for_mode(self.mode)

    def start_session(self) -> StepResult:
        """
        Initialize the session and return the first step.

        Returns:
            StepResult for the first step (status=pending).
        """
        first_step = self.steps[0]
        self.session.current_step = first_step.code
        self.session.current_part = 1
        self.session.status = "active"
        self.session.save(update_fields=["current_step", "current_part", "status"])

        step_result, _ = StepResult.objects.get_or_create(
            session=self.session,
            step_code=first_step.code,
            defaults={
                "step_name": first_step.name,
                "status": "pending",
            },
        )

        logger.info(
            "Session %d started in %s mode. First step: %s",
            self.session.pk,
            self.mode,
            first_step.code,
        )
        return step_result

    def submit_step(self, user_input: str) -> str:
        """
        Submit user input for the current step. Dispatches a Celery task.

        Args:
            user_input: The user's text input for this step.

        Returns:
            Celery task ID for polling.
        """
        step_def = get_step_def(self.mode, self.session.current_step)
        if step_def is None:
            raise ValueError(f"No step definition for code={self.session.current_step}")

        task = execute_ariz_step.delay(
            session_id=self.session.pk,
            step_code=step_def.code,
            user_input=user_input,
            step_name=step_def.name,
            validators=step_def.validators,
        )

        logger.info(
            "Step %s submitted for session %d. Task ID: %s",
            step_def.code,
            self.session.pk,
            task.id,
        )
        return task.id

    def advance_to_next(self) -> StepResult | None:
        """
        Advance to the next step after the current one is completed.

        Returns:
            StepResult for the next step, or None if session is complete.
        """
        current_step = self._get_current_step_result()
        if current_step and current_step.status != "completed":
            raise ValueError(
                f"Cannot advance: current step {current_step.step_code} "
                f"is {current_step.status}, not completed."
            )

        next_step_def = get_next_step(self.mode, self.session.current_step)
        if next_step_def is None:
            self._complete_session()
            return None

        self.session.current_step = next_step_def.code
        if next_step_def.code.startswith(("2.", "3.", "4.")):
            self.session.current_part = int(next_step_def.code[0])
        self.session.save(update_fields=["current_step", "current_part"])

        step_result, _ = StepResult.objects.get_or_create(
            session=self.session,
            step_code=next_step_def.code,
            defaults={
                "step_name": next_step_def.name,
                "status": "pending",
            },
        )

        logger.info("Advanced to step %s for session %d", next_step_def.code, self.session.pk)
        return step_result

    def go_back(self) -> StepResult | None:
        """
        Go back to the previous step.

        Returns:
            StepResult for the previous step, or None if at the start.
        """
        prev_step_def = get_previous_step(self.mode, self.session.current_step)
        if prev_step_def is None:
            return None

        self.session.current_step = prev_step_def.code
        self.session.save(update_fields=["current_step"])

        step_result = StepResult.objects.filter(
            session=self.session,
            step_code=prev_step_def.code,
        ).first()

        logger.info("Went back to step %s for session %d", prev_step_def.code, self.session.pk)
        return step_result

    def get_progress(self) -> dict:
        """
        Return session progress info.

        Returns:
            Dict with current_step, total_steps, percent, steps_completed.
        """
        total = len(self.steps)
        completed_codes = set(
            StepResult.objects.filter(
                session=self.session,
                status="completed",
            ).values_list("step_code", flat=True)
        )

        current_index = 0
        for i, step in enumerate(self.steps):
            if step.code == self.session.current_step:
                current_index = i
                break

        completed_count = len(completed_codes)
        percent = round(completed_count / total * 100) if total > 0 else 0

        return {
            "current_step": self.session.current_step,
            "current_step_name": self.steps[current_index].name if current_index < total else "",
            "current_index": current_index,
            "total_steps": total,
            "completed_count": completed_count,
            "percent": percent,
            "steps_completed": [
                {
                    "code": step.code,
                    "name": step.name,
                    "completed": step.code in completed_codes,
                }
                for step in self.steps
            ],
        }

    def get_session_summary(self) -> dict:
        """
        Return a full session summary.

        Returns:
            Dict with problem info, all steps, contradictions, IKR, solutions.
        """
        problem = self.session.problem

        steps = []
        for sr in self.session.steps.order_by("created_at"):
            steps.append({
                "code": sr.step_code,
                "name": sr.step_name,
                "status": sr.status,
                "user_input": sr.user_input,
                "result": sr.validated_result or sr.llm_output,
            })

        contradictions = []
        for c in self.session.contradictions.all():
            contradictions.append({
                "type": c.type,
                "quality_a": c.quality_a,
                "quality_b": c.quality_b,
                "property_s": c.property_s,
                "anti_property_s": c.anti_property_s,
                "formulation": c.formulation,
            })

        ikrs = []
        for ikr in self.session.ikrs.all():
            ikrs.append({
                "formulation": ikr.formulation,
                "strengthened_formulation": ikr.strengthened_formulation,
                "vpr_used": ikr.vpr_used,
            })

        solutions = []
        for sol in self.session.solutions.all():
            solutions.append({
                "title": sol.title,
                "description": sol.description,
                "method_used": sol.method_used,
                "novelty_score": sol.novelty_score,
                "feasibility_score": sol.feasibility_score,
            })

        return {
            "session_id": self.session.pk,
            "mode": self.mode,
            "status": self.session.status,
            "problem": {
                "id": problem.pk,
                "title": problem.title,
                "description": problem.original_description,
                "domain": problem.domain,
            },
            "progress": self.get_progress(),
            "steps": steps,
            "contradictions": contradictions,
            "ikrs": ikrs,
            "solutions": solutions,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_current_step_result(self) -> StepResult | None:
        """Get the StepResult for the current step."""
        return StepResult.objects.filter(
            session=self.session,
            step_code=self.session.current_step,
        ).first()

    def _complete_session(self) -> None:
        """Mark the session as completed."""
        self.session.status = "completed"
        self.session.completed_at = timezone.now()
        self.session.save(update_fields=["status", "completed_at"])

        self.session.problem.status = "completed"
        self.session.problem.save(update_fields=["status"])

        logger.info("Session %d completed.", self.session.pk)
