"""
Celery tasks for async LLM processing of ARIZ steps.
"""
import json
import logging
from typing import Any

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.ariz_engine.models import ARIZSession, StepResult
from apps.llm_service.client import OpenAIClient
from apps.llm_service.prompt_manager import PromptManager

logger = logging.getLogger(__name__)


def _build_context(session: ARIZSession, user_input: str) -> dict[str, Any]:
    """
    Build the template context from session data and previous step results.

    Returns a dict with keys: problem_title, problem_description, mode,
    user_input, previous_results, previous_steps, context_snapshot.
    """
    problem = session.problem
    previous_steps = (
        StepResult.objects.filter(session=session, status="completed")
        .order_by("created_at")
    )

    # Format previous results into a readable block
    previous_results_parts: list[str] = []
    previous_steps_data: list[dict[str, str]] = []
    for step in previous_steps:
        result_text = step.validated_result or step.llm_output
        previous_results_parts.append(
            f"### Step {step.step_code}: {step.step_name}\n{result_text}"
        )
        previous_steps_data.append({
            "step_code": step.step_code,
            "step_name": step.step_name,
            "user_input": step.user_input,
            "result": result_text,
        })

    return {
        "problem_title": problem.title,
        "problem_description": problem.original_description,
        "domain": problem.domain,
        "mode": session.mode,
        "current_step": session.current_step,
        "user_input": user_input,
        "previous_results": "\n\n".join(previous_results_parts),
        "previous_steps": previous_steps_data,
        "context_snapshot": session.context_snapshot or {},
    }


def _run_validation(
    client: OpenAIClient,
    prompt_manager: PromptManager,
    validators: list[str],
    llm_output: str,
    context: dict[str, Any],
) -> tuple[str, str]:
    """
    Run validation prompts against the LLM output.

    Returns:
        Tuple of (validated_result, validation_notes).
        validated_result is the original output if valid, or a refined version.
    """
    if not validators:
        return llm_output, ""

    validation_prompt = prompt_manager.render_validation_prompt(
        rule_codes=validators,
        content=llm_output,
        context=context,
    )

    system_prompt = (
        "You are a TRIZ validation expert. Check the provided ARIZ step output "
        "for correctness according to the specified rules. "
        "Respond with a JSON object: "
        '{"valid": true/false, "issues": [...], "suggestions": [...], '
        '"corrected_output": "..." (only if valid is false)}. '
        "Respond in Russian."
    )

    try:
        response = client.send_validation(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": validation_prompt}],
        )

        # Parse validation response
        validation_data = _parse_validation_response(response.content)

        if validation_data.get("valid", True):
            notes = ""
            if validation_data.get("suggestions"):
                notes = "Suggestions: " + "; ".join(validation_data["suggestions"])
            return llm_output, notes

        # Validation failed — use corrected output if available
        corrected = validation_data.get("corrected_output", "")
        issues = validation_data.get("issues", [])
        notes = "Issues: " + "; ".join(issues) if issues else "Validation failed"

        return corrected or llm_output, notes

    except Exception as exc:
        logger.warning("Validation failed with error: %s. Proceeding without validation.", exc)
        return llm_output, f"Validation skipped due to error: {exc}"


def _parse_validation_response(content: str) -> dict[str, Any]:
    """
    Try to parse JSON from the validation LLM response.
    Handles cases where JSON is wrapped in markdown code blocks.
    """
    text = content.strip()

    # Remove markdown code block markers if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        if lines[-1].strip() == "```":
            lines = lines[1:-1]
        else:
            lines = lines[1:]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Could not parse validation response as JSON: %s...", text[:200])
        return {"valid": True, "issues": [], "suggestions": []}


def _update_context_snapshot(
    session: ARIZSession,
    step_code: str,
    user_input: str,
    result: str,
) -> None:
    """
    Update the session's context_snapshot with the latest step result.
    """
    snapshot = session.context_snapshot or {}
    steps_data = snapshot.get("steps", {})
    steps_data[step_code] = {
        "user_input": user_input,
        "result": result,
        "completed_at": timezone.now().isoformat(),
    }
    snapshot["steps"] = steps_data
    snapshot["last_completed_step"] = step_code
    session.context_snapshot = snapshot
    session.save(update_fields=["context_snapshot"])


@shared_task(
    max_retries=2,
    default_retry_delay=10,
    acks_late=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    name="llm_service.execute_ariz_step",
)
def execute_ariz_step(
    session_id: int,
    step_code: str,
    user_input: str,
    step_name: str = "",
    validators: list[str] | None = None,
) -> dict[str, Any]:
    """
    Celery task: execute one ARIZ step via OpenAI API.

    Workflow:
        1. Load session context (previous steps)
        2. Render system + step prompts via PromptManager
        3. Call OpenAI API (GPT-4o)
        4. Run validation (GPT-4o-mini) if validators are specified
        5. Save StepResult to database
        6. Update session context_snapshot

    Args:
        session_id: ARIZSession primary key.
        step_code: Step identifier (e.g. "1", "1.1").
        user_input: User's input for this step.
        step_name: Human-readable step name.
        validators: List of validator codes (e.g. ["falseness_check"]).

    Returns:
        Dict with step result data.
    """
    validators = validators or []

    logger.info(
        "Executing ARIZ step: session=%d step=%s validators=%s",
        session_id,
        step_code,
        validators,
    )

    try:
        session = ARIZSession.objects.select_related("problem").get(pk=session_id)
    except ARIZSession.DoesNotExist:
        logger.error("ARIZSession %d does not exist", session_id)
        raise

    # Get or create StepResult record
    step_result, created = StepResult.objects.get_or_create(
        session=session,
        step_code=step_code,
        defaults={
            "step_name": step_name or f"Step {step_code}",
            "user_input": user_input,
            "status": "in_progress",
        },
    )
    if not created:
        step_result.user_input = user_input
        step_result.status = "in_progress"
        step_result.save(update_fields=["user_input", "status"])

    try:
        # 1. Build context
        context = _build_context(session, user_input)

        # 2. Render prompts
        prompt_manager = PromptManager()
        system_prompt = prompt_manager.render_system_prompt(mode=session.mode)
        step_prompt = prompt_manager.render_step_prompt(
            step_code=step_code,
            context=context,
            mode=session.mode,
        )

        # 3. Call OpenAI
        client = OpenAIClient()
        llm_response = client.send_message(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": step_prompt}],
        )

        llm_output = llm_response.content

        # 4. Validate
        validated_result, validation_notes = _run_validation(
            client=client,
            prompt_manager=prompt_manager,
            validators=validators,
            llm_output=llm_output,
            context=context,
        )

        # 5. Save StepResult
        with transaction.atomic():
            step_result.llm_output = llm_output
            step_result.validated_result = validated_result
            step_result.validation_notes = validation_notes
            step_result.status = "completed"
            step_result.save(update_fields=[
                "llm_output",
                "validated_result",
                "validation_notes",
                "status",
            ])

            # 6. Update context snapshot
            _update_context_snapshot(
                session, step_code, user_input, validated_result or llm_output
            )

        logger.info(
            "Step %s completed: tokens_in=%d tokens_out=%d cost=$%.6f",
            step_code,
            llm_response.input_tokens,
            llm_response.output_tokens,
            llm_response.cost_usd,
        )

        return {
            "session_id": session_id,
            "step_code": step_code,
            "step_name": step_result.step_name,
            "status": "completed",
            "llm_output": llm_output,
            "validated_result": validated_result,
            "validation_notes": validation_notes,
            "input_tokens": llm_response.input_tokens,
            "output_tokens": llm_response.output_tokens,
            "cost_usd": llm_response.cost_usd,
        }

    except Exception as exc:
        logger.exception("Failed to execute step %s for session %d", step_code, session_id)
        step_result.status = "failed"
        step_result.validation_notes = f"Error: {exc}"
        step_result.save(update_fields=["status", "validation_notes"])

        # Re-raise for Celery autoretry mechanism
        raise
