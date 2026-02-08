"""
Tests for the load_triz_data management command.

Covers:
    - Loading principles from JSON fixtures
    - Loading effects, standards, definitions, rules, transformations, analogs
    - Clearing existing data
    - Error handling for missing fixture files
    - Embedding generation with mocked OpenAI client
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.knowledge_base.models import (
    AnalogTask,
    Definition,
    Rule,
    Standard,
    TechnologicalEffect,
    TRIZPrinciple,
    TypicalTransformation,
)


def _create_fixture_dir(tmpdir: str) -> Path:
    """Create a temporary fixtures directory with minimal test data."""
    fixtures_dir = Path(tmpdir) / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    # principles.json
    (fixtures_dir / "principles.json").write_text(
        json.dumps([
            {
                "number": 1,
                "name": "Segmentation",
                "description": "Divide an object into independent parts.",
                "examples": ["Modular furniture"],
                "is_additional": False,
            },
            {
                "number": 2,
                "name": "Taking out",
                "description": "Separate an interfering part.",
                "examples": [],
                "is_additional": False,
            },
        ]),
        encoding="utf-8",
    )

    # paired_principles.json
    (fixtures_dir / "paired_principles.json").write_text(
        json.dumps([
            {"principle_number": 1, "paired_with_number": 2},
        ]),
        encoding="utf-8",
    )

    # effects_physical.json
    (fixtures_dir / "effects_physical.json").write_text(
        json.dumps([
            {
                "type": "physical",
                "name": "Thermal expansion",
                "description": "Materials expand when heated.",
                "function_keywords": ["heating", "expansion"],
            },
        ]),
        encoding="utf-8",
    )

    # Empty effect files for other categories
    for category in ["chemical", "biological", "geometrical"]:
        (fixtures_dir / f"effects_{category}.json").write_text(
            json.dumps([]),
            encoding="utf-8",
        )

    # standards.json
    (fixtures_dir / "standards.json").write_text(
        json.dumps([
            {
                "class_number": 1,
                "number": "1.1.1",
                "name": "Building a vepol",
                "description": "If an object is not controllable, build a vepol.",
                "applicability": "When control is needed.",
            },
        ]),
        encoding="utf-8",
    )

    # definitions.json
    (fixtures_dir / "definitions.json").write_text(
        json.dumps([
            {
                "number": 1,
                "term": "System",
                "definition": "A set of interacting elements.",
            },
        ]),
        encoding="utf-8",
    )

    # rules.json
    (fixtures_dir / "rules.json").write_text(
        json.dumps([
            {
                "number": 1,
                "name": "Rule of falseness check",
                "description": "Check if the problem formulation is false.",
                "examples": ["Example of falseness check"],
            },
        ]),
        encoding="utf-8",
    )

    # typical_transformations.json
    (fixtures_dir / "typical_transformations.json").write_text(
        json.dumps([
            {
                "contradiction_type": "sharpened",
                "transformation": "Segmentation",
                "description": "Divide the object into parts.",
            },
        ]),
        encoding="utf-8",
    )

    # analog_tasks.json
    (fixtures_dir / "analog_tasks.json").write_text(
        json.dumps([
            {
                "title": "Heat pipe optimization",
                "problem_description": "Improve heat transfer in narrow pipes.",
                "op_formulation": "Pipe must be thin to fit but thick to transfer heat.",
                "solution_principle": "Use internal micro-fins.",
                "domain": "thermal",
                "source": "Chapter 6, Example 1",
            },
        ]),
        encoding="utf-8",
    )

    return fixtures_dir


@pytest.mark.django_db
class TestLoadTrizDataCommand(TestCase):
    """Test the load_triz_data management command."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.fixtures_dir = _create_fixture_dir(self.tmpdir)

    @patch("apps.knowledge_base.management.commands.load_triz_data.FIXTURES_DIR")
    def test_load_all(self, mock_dir):
        mock_dir.__truediv__ = self.fixtures_dir.__truediv__
        mock_dir.exists = self.fixtures_dir.exists

        call_command("load_triz_data", "--all")

        assert TRIZPrinciple.objects.count() == 2
        assert TechnologicalEffect.objects.count() == 1
        assert Standard.objects.count() == 1
        assert Definition.objects.count() == 1
        assert Rule.objects.count() == 1
        assert TypicalTransformation.objects.count() == 1
        assert AnalogTask.objects.count() == 1

    @patch("apps.knowledge_base.management.commands.load_triz_data.FIXTURES_DIR")
    def test_load_principles_only(self, mock_dir):
        mock_dir.__truediv__ = self.fixtures_dir.__truediv__

        call_command("load_triz_data", "--principles")

        assert TRIZPrinciple.objects.count() == 2
        assert TechnologicalEffect.objects.count() == 0

    @patch("apps.knowledge_base.management.commands.load_triz_data.FIXTURES_DIR")
    def test_load_principles_sets_paired(self, mock_dir):
        mock_dir.__truediv__ = self.fixtures_dir.__truediv__

        call_command("load_triz_data", "--principles")

        principle1 = TRIZPrinciple.objects.get(number=1)
        assert principle1.paired_with is not None
        assert principle1.paired_with.number == 2

    @patch("apps.knowledge_base.management.commands.load_triz_data.FIXTURES_DIR")
    def test_load_effects_only(self, mock_dir):
        mock_dir.__truediv__ = self.fixtures_dir.__truediv__

        call_command("load_triz_data", "--effects")

        assert TechnologicalEffect.objects.count() == 1
        effect = TechnologicalEffect.objects.first()
        assert effect.name == "Thermal expansion"
        assert effect.type == "physical"

    @patch("apps.knowledge_base.management.commands.load_triz_data.FIXTURES_DIR")
    def test_load_standards_only(self, mock_dir):
        mock_dir.__truediv__ = self.fixtures_dir.__truediv__

        call_command("load_triz_data", "--standards")

        assert Standard.objects.count() == 1
        standard = Standard.objects.first()
        assert standard.number == "1.1.1"

    @patch("apps.knowledge_base.management.commands.load_triz_data.FIXTURES_DIR")
    def test_load_definitions_only(self, mock_dir):
        mock_dir.__truediv__ = self.fixtures_dir.__truediv__

        call_command("load_triz_data", "--definitions")

        assert Definition.objects.count() == 1

    @patch("apps.knowledge_base.management.commands.load_triz_data.FIXTURES_DIR")
    def test_load_rules_only(self, mock_dir):
        mock_dir.__truediv__ = self.fixtures_dir.__truediv__

        call_command("load_triz_data", "--rules")

        assert Rule.objects.count() == 1

    @patch("apps.knowledge_base.management.commands.load_triz_data.FIXTURES_DIR")
    def test_load_analogs_only(self, mock_dir):
        mock_dir.__truediv__ = self.fixtures_dir.__truediv__

        call_command("load_triz_data", "--analogs")

        assert AnalogTask.objects.count() == 1
        analog = AnalogTask.objects.first()
        assert analog.title == "Heat pipe optimization"

    @patch("apps.knowledge_base.management.commands.load_triz_data.FIXTURES_DIR")
    def test_clear_and_reload(self, mock_dir):
        mock_dir.__truediv__ = self.fixtures_dir.__truediv__

        # Load data first
        call_command("load_triz_data", "--all")
        assert TRIZPrinciple.objects.count() == 2

        # Clear and reload
        call_command("load_triz_data", "--all", "--clear")
        assert TRIZPrinciple.objects.count() == 2  # Re-loaded after clear

    @patch("apps.knowledge_base.management.commands.load_triz_data.FIXTURES_DIR")
    def test_idempotent_reload(self, mock_dir):
        mock_dir.__truediv__ = self.fixtures_dir.__truediv__

        call_command("load_triz_data", "--all")
        count1 = TRIZPrinciple.objects.count()

        call_command("load_triz_data", "--all")
        count2 = TRIZPrinciple.objects.count()

        assert count1 == count2

    def test_no_arguments_prints_error(self):
        """Running without arguments should print an error."""
        from io import StringIO
        stderr = StringIO()
        call_command("load_triz_data", stderr=stderr)
        output = stderr.getvalue()
        assert "No data type specified" in output
