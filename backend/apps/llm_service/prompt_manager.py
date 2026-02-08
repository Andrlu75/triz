"""
Jinja2-based prompt template manager for ARIZ steps.
"""
import logging
from pathlib import Path
from typing import Any

from django.conf import settings
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

logger = logging.getLogger(__name__)

# Mode-to-audience mapping
MODE_AUDIENCE_MAP = {
    "express": "b2c",
    "full": "b2b",
    "autopilot": "b2c",
}

# Mode-to-step-directory mapping
MODE_STEP_DIR_MAP = {
    "express": "steps/express",
    "full": "steps/full",
    "autopilot": "steps/autopilot",
}


class PromptManager:
    """
    Loads and renders Jinja2 prompt templates for ARIZ sessions.

    Template directory structure (under settings.PROMPTS_DIR)::

        prompts/
        +-- system/
        |   +-- master.j2
        |   +-- role.j2
        |   +-- methodology.j2
        +-- steps/
        |   +-- express/step_1.j2 ... step_7.j2
        |   +-- full/step_1_1.j2 ... step_4_8.j2
        |   +-- autopilot/full_analysis.j2
        +-- validation/
        |   +-- validate_falseness.j2
        |   +-- validate_terms.j2
        |   +-- ...
        +-- adapters/
            +-- b2c.j2
            +-- b2b.j2
    """

    def __init__(self, prompts_dir: str | Path | None = None) -> None:
        self._prompts_dir = Path(
            prompts_dir or getattr(settings, "PROMPTS_DIR", Path(settings.BASE_DIR) / "prompts")
        )
        self._env = Environment(
            loader=FileSystemLoader(str(self._prompts_dir)),
            autoescape=False,
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render_system_prompt(
        self,
        mode: str = "express",
        audience: str | None = None,
    ) -> str:
        """
        Assemble the full system prompt from master + role + methodology + adapter.

        Args:
            mode: ARIZ mode ("express", "full", "autopilot").
            audience: Audience adapter ("b2c" or "b2b"). Auto-detected from mode if omitted.

        Returns:
            Rendered system prompt string.
        """
        resolved_audience = audience or MODE_AUDIENCE_MAP.get(mode, "b2c")

        parts: list[str] = []

        # Master prompt
        master = self._render_optional("system/master.j2", {"mode": mode, "audience": resolved_audience})
        if master:
            parts.append(master)

        # Role prompt
        role = self._render_optional("system/role.j2", {"mode": mode})
        if role:
            parts.append(role)

        # Methodology prompt
        methodology = self._render_optional(
            "system/methodology.j2", {"mode": mode, "audience": resolved_audience}
        )
        if methodology:
            parts.append(methodology)

        # Audience adapter
        adapter = self._render_optional(
            f"adapters/{resolved_audience}.j2", {"mode": mode}
        )
        if adapter:
            parts.append(adapter)

        result = "\n\n".join(parts)
        if not result:
            logger.warning(
                "System prompt is empty for mode=%s audience=%s. "
                "Ensure templates exist in %s",
                mode,
                resolved_audience,
                self._prompts_dir,
            )
            result = self._default_system_prompt(mode, resolved_audience)

        return result

    def render_step_prompt(
        self,
        step_code: str,
        context: dict[str, Any],
        mode: str = "express",
    ) -> str:
        """
        Render the prompt template for a specific ARIZ step.

        Args:
            step_code: Step identifier (e.g. "1", "1.1", "full_analysis").
            context: Template variables (user_input, previous_steps, problem, etc.).
            mode: ARIZ mode to determine template directory.

        Returns:
            Rendered step prompt string.
        """
        step_dir = MODE_STEP_DIR_MAP.get(mode, "steps/express")

        # Normalize step code for file name: "1.1" -> "step_1_1.j2", "1" -> "step_1.j2"
        if mode == "autopilot":
            template_name = f"{step_dir}/full_analysis.j2"
        else:
            safe_code = step_code.replace(".", "_")
            template_name = f"{step_dir}/step_{safe_code}.j2"

        rendered = self._render_optional(template_name, context)
        if rendered:
            return rendered

        # Fallback: generate a default prompt
        logger.warning(
            "Step template %s not found, using default prompt for step %s",
            template_name,
            step_code,
        )
        return self._default_step_prompt(step_code, context)

    def render_validation_prompt(
        self,
        rule_codes: list[str],
        content: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        Render validation prompt(s) for given rule codes.

        Args:
            rule_codes: List of validator identifiers, e.g. ["falseness_check", "terms_check"].
            content: The LLM output to validate.
            context: Additional template variables.

        Returns:
            Combined validation prompt string.
        """
        ctx = dict(context or {})
        ctx["content"] = content

        parts: list[str] = []
        for code in rule_codes:
            template_name = f"validation/validate_{code.replace('_check', '')}.j2"
            rendered = self._render_optional(template_name, ctx)
            if rendered:
                parts.append(rendered)
            else:
                parts.append(self._default_validation_prompt(code, content))

        return "\n\n---\n\n".join(parts)

    def template_exists(self, template_name: str) -> bool:
        """Check whether a template file exists."""
        try:
            self._env.get_template(template_name)
            return True
        except TemplateNotFound:
            return False

    def list_templates(self, prefix: str = "") -> list[str]:
        """List all template names matching an optional prefix."""
        all_templates = self._env.loader.list_templates()  # type: ignore[union-attr]
        if prefix:
            return [t for t in all_templates if t.startswith(prefix)]
        return list(all_templates)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _render_optional(self, template_name: str, context: dict[str, Any]) -> str:
        """Render a template if it exists, otherwise return empty string."""
        try:
            template = self._env.get_template(template_name)
            return template.render(**context).strip()
        except TemplateNotFound:
            logger.debug("Template %s not found, skipping", template_name)
            return ""

    @staticmethod
    def _default_system_prompt(mode: str, audience: str) -> str:
        """Fallback system prompt when templates are not yet created."""
        audience_desc = (
            "Use simple everyday language without TRIZ jargon."
            if audience == "b2c"
            else "Use professional TRIZ terminology."
        )
        return (
            f"You are an expert TRIZ (Theory of Inventive Problem Solving) consultant "
            f"with 30 years of experience. You are guiding a user through the ARIZ-2010 "
            f"methodology in '{mode}' mode.\n\n"
            f"{audience_desc}\n\n"
            f"Respond in Russian. Be structured and clear. "
            f"Use numbered lists and markdown formatting."
        )

    @staticmethod
    def _default_step_prompt(step_code: str, context: dict[str, Any]) -> str:
        """Fallback step prompt when the template file is missing."""
        user_input = context.get("user_input", "")
        problem_title = context.get("problem_title", "")
        problem_description = context.get("problem_description", "")
        previous_results = context.get("previous_results", "")

        prompt_parts = [
            f"## ARIZ Step {step_code}\n",
        ]
        if problem_title:
            prompt_parts.append(f"**Problem:** {problem_title}")
        if problem_description:
            prompt_parts.append(f"**Description:** {problem_description}")
        if previous_results:
            prompt_parts.append(f"**Previous analysis:**\n{previous_results}")
        if user_input:
            prompt_parts.append(f"**User input:**\n{user_input}")

        prompt_parts.append(
            "\nAnalyze the information above and provide a structured response "
            "for this ARIZ step. Be thorough and specific."
        )
        return "\n\n".join(prompt_parts)

    @staticmethod
    def _default_validation_prompt(code: str, content: str) -> str:
        """Fallback validation prompt when the template file is missing."""
        return (
            f"## Validation: {code}\n\n"
            f"Review the following ARIZ analysis output and check it for correctness.\n\n"
            f"**Content to validate:**\n{content}\n\n"
            f"Respond with a JSON object:\n"
            f'{{"valid": true/false, "issues": ["list of issues if any"], '
            f'"suggestions": ["list of suggestions"]}}'
        )
