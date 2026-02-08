"""
Autopilot mode — LLM automatically passes through all ARIZ steps.

1-3 LLM calls with extended context. Returns a structured report.
"""
import logging

from apps.ariz_engine.models import ARIZSession, Solution, StepResult
from apps.llm_service.client import OpenAIClient
from apps.llm_service.prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class AutopilotMode:
    """
    Autopilot ARIZ mode — LLM solves the problem automatically.

    The LLM runs through an abbreviated analysis in 1-3 API calls
    and returns a structured report with contradictions, IKR, and solutions.
    """

    MODE_NAME = "autopilot"
    AUDIENCE = "b2c"

    def __init__(self, session: ARIZSession):
        self.session = session
        self.client = OpenAIClient()
        self.prompt_manager = PromptManager()

    def run(self) -> dict:
        """
        Execute the full autopilot analysis.

        Returns:
            Dict with analysis results: steps, contradictions, solutions.
        """
        problem = self.session.problem

        system_prompt = self.prompt_manager.render_system_prompt(
            mode="autopilot",
            audience=self.AUDIENCE,
        )

        context = {
            "problem_title": problem.title,
            "problem_description": problem.original_description,
            "domain": problem.domain,
            "mode": "autopilot",
        }

        step_prompt = self.prompt_manager.render_step_prompt(
            step_code="full_analysis",
            context=context,
            mode="autopilot",
        )

        # Single comprehensive LLM call
        response = self.client.send_message(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": step_prompt}],
            max_tokens=8192,
            temperature=0.7,
        )

        # Save as a single step result
        StepResult.objects.update_or_create(
            session=self.session,
            step_code="auto",
            defaults={
                "step_name": "Autopilot Analysis",
                "user_input": problem.original_description,
                "llm_output": response.content,
                "validated_result": response.content,
                "status": "completed",
            },
        )

        # Update session
        self.session.status = "completed"
        self.session.context_snapshot = {
            "autopilot_result": response.content,
            "cost_usd": response.cost_usd,
        }
        self.session.save(update_fields=["status", "context_snapshot"])

        logger.info(
            "Autopilot completed for session %d (cost: $%.4f)",
            self.session.pk,
            response.cost_usd,
        )

        return {
            "session_id": self.session.pk,
            "analysis": response.content,
            "cost_usd": response.cost_usd,
            "tokens_used": response.total_tokens,
        }
