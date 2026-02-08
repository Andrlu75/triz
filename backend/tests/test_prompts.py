"""
Tests for the PromptManager (apps.llm_service.prompt_manager).

Tests cover template rendering, fallback behavior, and edge cases.
"""
import os
import tempfile
from pathlib import Path

import pytest

from apps.llm_service.prompt_manager import (
    MODE_AUDIENCE_MAP,
    MODE_STEP_DIR_MAP,
    PromptManager,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_prompts_dir():
    """Create a temporary directory with sample Jinja2 templates."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # system templates
        (base / "system").mkdir(parents=True)
        (base / "system" / "master.j2").write_text(
            "You are guiding a user in {{ mode }} mode for {{ audience }} audience."
        )
        (base / "system" / "role.j2").write_text(
            "Role: Expert TRIZ consultant. Mode: {{ mode }}."
        )
        (base / "system" / "methodology.j2").write_text(
            "ARIZ methodology overview for {{ mode }} mode."
        )

        # adapters
        (base / "adapters").mkdir(parents=True)
        (base / "adapters" / "b2c.j2").write_text(
            "Use simple everyday language. Mode: {{ mode }}."
        )
        (base / "adapters" / "b2b.j2").write_text(
            "Use professional TRIZ terminology. Mode: {{ mode }}."
        )

        # express step templates
        (base / "steps" / "express").mkdir(parents=True)
        for i in range(1, 8):
            (base / "steps" / "express" / f"step_{i}.j2").write_text(
                f"Express step {i}: Analyze '{{{{ problem_description }}}}'. "
                f"User said: '{{{{ user_input }}}}'."
            )

        # full step template (sample)
        (base / "steps" / "full").mkdir(parents=True)
        (base / "steps" / "full" / "step_1_1.j2").write_text(
            "Full ARIZ step 1.1: Mini-task. Problem: {{ problem_description }}."
        )

        # autopilot template
        (base / "steps" / "autopilot").mkdir(parents=True)
        (base / "steps" / "autopilot" / "full_analysis.j2").write_text(
            "Autopilot full analysis: {{ problem_description }}."
        )

        # validation templates
        (base / "validation").mkdir(parents=True)
        (base / "validation" / "validate_falseness.j2").write_text(
            "Check for falseness in: {{ content }}."
        )
        (base / "validation" / "validate_terms.j2").write_text(
            "Check terms in: {{ content }}."
        )

        yield tmpdir


@pytest.fixture
def pm(temp_prompts_dir):
    """Create a PromptManager instance with temporary templates."""
    return PromptManager(prompts_dir=temp_prompts_dir)


@pytest.fixture
def empty_pm():
    """Create a PromptManager with an empty (non-existent) prompts directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        empty_dir = Path(tmpdir) / "nonexistent"
        empty_dir.mkdir()
        yield PromptManager(prompts_dir=str(empty_dir))


# ---------------------------------------------------------------------------
# render_system_prompt tests
# ---------------------------------------------------------------------------


class TestRenderSystemPrompt:
    """Tests for system prompt assembly."""

    def test_express_b2c_prompt(self, pm):
        """Express mode with b2c audience should combine master, role, methodology, and adapter."""
        result = pm.render_system_prompt(mode="express", audience="b2c")

        assert "express" in result.lower() or "express" in result
        assert "b2c" in result
        assert "Role: Expert TRIZ consultant" in result
        assert "ARIZ methodology" in result
        assert "simple everyday language" in result

    def test_full_b2b_prompt(self, pm):
        """Full mode with b2b audience should include b2b adapter."""
        result = pm.render_system_prompt(mode="full", audience="b2b")

        assert "full" in result
        assert "professional TRIZ terminology" in result

    def test_auto_audience_detection(self, pm):
        """Audience should be auto-detected from mode if not specified."""
        # express -> b2c
        result_express = pm.render_system_prompt(mode="express")
        assert "simple everyday language" in result_express

        # full -> b2b
        result_full = pm.render_system_prompt(mode="full")
        assert "professional TRIZ terminology" in result_full

    def test_all_four_parts_present(self, pm):
        """System prompt should combine all four template parts."""
        result = pm.render_system_prompt(mode="express", audience="b2c")
        # Split by double newline to check we got multiple parts
        parts = result.split("\n\n")
        assert len(parts) >= 3  # master, role, methodology, adapter

    def test_fallback_on_empty_templates(self, empty_pm):
        """Should fall back to default prompt when no templates exist."""
        result = empty_pm.render_system_prompt(mode="express", audience="b2c")
        assert len(result) > 0
        assert "TRIZ" in result

    def test_audience_map_coverage(self):
        """All expected modes should have audience mappings."""
        assert "express" in MODE_AUDIENCE_MAP
        assert "full" in MODE_AUDIENCE_MAP
        assert "autopilot" in MODE_AUDIENCE_MAP


# ---------------------------------------------------------------------------
# render_step_prompt tests
# ---------------------------------------------------------------------------


class TestRenderStepPrompt:
    """Tests for step prompt rendering."""

    def test_express_step_render(self, pm):
        """Should render an express step template with context."""
        context = {
            "problem_description": "The bridge is too weak.",
            "user_input": "The load exceeded capacity.",
        }
        result = pm.render_step_prompt(step_code="1", context=context, mode="express")

        assert "bridge is too weak" in result
        assert "load exceeded capacity" in result

    def test_all_express_steps_available(self, pm):
        """All 7 express step templates should render without error."""
        context = {"problem_description": "Test problem", "user_input": "Test input"}
        for i in range(1, 8):
            result = pm.render_step_prompt(step_code=str(i), context=context, mode="express")
            assert len(result) > 0, f"Step {i} rendered empty"

    def test_full_step_render(self, pm):
        """Should render a full ARIZ step template (step_1_1)."""
        context = {"problem_description": "Technical challenge"}
        result = pm.render_step_prompt(step_code="1.1", context=context, mode="full")
        assert "Technical challenge" in result

    def test_autopilot_mode(self, pm):
        """Autopilot mode should use the full_analysis template."""
        context = {"problem_description": "Automated analysis"}
        result = pm.render_step_prompt(step_code="auto", context=context, mode="autopilot")
        assert "Automated analysis" in result

    def test_step_code_normalization(self, pm):
        """Step code dots should be replaced with underscores in filenames."""
        context = {"problem_description": "Test"}
        # "1.1" -> "step_1_1.j2"
        result = pm.render_step_prompt(step_code="1.1", context=context, mode="full")
        assert len(result) > 0

    def test_missing_template_fallback(self, pm):
        """Should return fallback prompt for non-existent step templates."""
        context = {"problem_description": "Test problem", "user_input": "My input"}
        result = pm.render_step_prompt(step_code="99", context=context, mode="express")
        # Should still return something useful (fallback)
        assert len(result) > 0
        assert "99" in result or "Step" in result

    def test_mode_directory_map(self):
        """All modes should have step directory mappings."""
        assert "express" in MODE_STEP_DIR_MAP
        assert "full" in MODE_STEP_DIR_MAP
        assert "autopilot" in MODE_STEP_DIR_MAP


# ---------------------------------------------------------------------------
# render_validation_prompt tests
# ---------------------------------------------------------------------------


class TestRenderValidationPrompt:
    """Tests for validation prompt rendering."""

    def test_single_rule(self, pm):
        """Should render a single validation rule template."""
        result = pm.render_validation_prompt(
            rule_codes=["falseness_check"],
            content="Some analysis output.",
        )
        assert "Some analysis output" in result

    def test_multiple_rules(self, pm):
        """Multiple rules should be joined with separator."""
        result = pm.render_validation_prompt(
            rule_codes=["falseness_check", "terms_check"],
            content="Content to validate.",
        )
        assert "---" in result  # separator between rules
        assert "Content to validate" in result

    def test_missing_rule_fallback(self, pm):
        """Should use fallback for unknown validation rules."""
        result = pm.render_validation_prompt(
            rule_codes=["unknown_rule"],
            content="Some content.",
        )
        # Should still produce something (fallback)
        assert len(result) > 0
        assert "Some content" in result

    def test_empty_rules(self, pm):
        """Empty rule list should return empty string."""
        result = pm.render_validation_prompt(rule_codes=[], content="Test")
        assert result == ""

    def test_rule_code_stripping(self, pm):
        """Rule codes ending in _check should have suffix stripped for template lookup."""
        # "falseness_check" -> "validate_falseness.j2"
        result = pm.render_validation_prompt(
            rule_codes=["falseness_check"],
            content="Check this.",
        )
        assert "Check this" in result


# ---------------------------------------------------------------------------
# template_exists tests
# ---------------------------------------------------------------------------


class TestTemplateExists:
    """Tests for the template_exists helper."""

    def test_existing_template(self, pm):
        """Should return True for templates that exist."""
        assert pm.template_exists("system/master.j2") is True

    def test_nonexistent_template(self, pm):
        """Should return False for missing templates."""
        assert pm.template_exists("system/nonexistent.j2") is False

    def test_step_template_exists(self, pm):
        """Should find step templates."""
        assert pm.template_exists("steps/express/step_1.j2") is True
        assert pm.template_exists("steps/express/step_99.j2") is False


# ---------------------------------------------------------------------------
# list_templates tests
# ---------------------------------------------------------------------------


class TestListTemplates:
    """Tests for template listing."""

    def test_list_all(self, pm):
        """Should list all templates in the prompts directory."""
        templates = pm.list_templates()
        assert len(templates) > 0

    def test_list_with_prefix(self, pm):
        """Should filter templates by prefix."""
        system_templates = pm.list_templates(prefix="system/")
        assert len(system_templates) >= 3
        assert all(t.startswith("system/") for t in system_templates)

    def test_list_step_templates(self, pm):
        """Should list step templates for a given mode."""
        express_templates = pm.list_templates(prefix="steps/express/")
        assert len(express_templates) == 7


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases and robustness."""

    def test_empty_context(self, pm):
        """Step prompt should handle empty context gracefully."""
        result = pm.render_step_prompt(step_code="1", context={}, mode="express")
        assert len(result) > 0

    def test_special_characters_in_context(self, pm):
        """Templates should handle special characters in context variables."""
        context = {
            "problem_description": 'Problem with "quotes" & <angle> brackets',
            "user_input": "Test {{ not_a_var }}",
        }
        # autoescape=False, so no escaping — Jinja2 should render but {{ not_a_var }} is a var reference
        # The test verifies no crash occurs
        result = pm.render_step_prompt(step_code="1", context=context, mode="express")
        assert len(result) > 0

    def test_unicode_in_context(self, pm):
        """Templates should handle Russian/Unicode text properly."""
        context = {
            "problem_description": "Проблема: мост слишком слабый для нагрузки.",
            "user_input": "Необходимо увеличить прочность конструкции.",
        }
        result = pm.render_step_prompt(step_code="1", context=context, mode="express")
        assert "мост" in result
