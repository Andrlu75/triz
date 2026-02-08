"""
Management command to load TRIZ knowledge base data from JSON fixtures.

Usage:
    python manage.py load_triz_data --all
    python manage.py load_triz_data --principles --standards
    python manage.py load_triz_data --all --generate-embeddings
"""

import json
import logging
import os
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.knowledge_base.models import (
    AnalogTask,
    Definition,
    Rule,
    Standard,
    TechnologicalEffect,
    TRIZPrinciple,
    TypicalTransformation,
)

logger = logging.getLogger(__name__)

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures"


class Command(BaseCommand):
    help = "Load TRIZ knowledge base data from JSON fixture files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Load all TRIZ data (principles, effects, standards, definitions, rules, transformations, analogs)",
        )
        parser.add_argument(
            "--principles",
            action="store_true",
            help="Load 50 inventive principles and paired principles",
        )
        parser.add_argument(
            "--effects",
            action="store_true",
            help="Load technological effects (physical, chemical, biological, geometrical)",
        )
        parser.add_argument(
            "--standards",
            action="store_true",
            help="Load 76 TRIZ standards",
        )
        parser.add_argument(
            "--definitions",
            action="store_true",
            help="Load 35 TRIZ definitions",
        )
        parser.add_argument(
            "--rules",
            action="store_true",
            help="Load 28 ARIZ rules",
        )
        parser.add_argument(
            "--transformations",
            action="store_true",
            help="Load typical transformations for resolving contradictions",
        )
        parser.add_argument(
            "--analogs",
            action="store_true",
            help="Load analog tasks from Chapter 6",
        )
        parser.add_argument(
            "--embeddings",
            action="store_true",
            help="Generate embeddings for effects and analog tasks via OpenAI API",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before loading",
        )

    def handle(self, *args, **options):
        load_all = options["all"]

        if not any([
            load_all,
            options["principles"],
            options["effects"],
            options["standards"],
            options["definitions"],
            options["rules"],
            options["transformations"],
            options["analogs"],
            options["embeddings"],
        ]):
            self.stderr.write(
                self.style.ERROR(
                    "No data type specified. Use --all or specify individual types."
                )
            )
            return

        if options["clear"]:
            self._clear_data()

        if load_all or options["principles"]:
            self._load_principles()

        if load_all or options["effects"]:
            self._load_effects()

        if load_all or options["standards"]:
            self._load_standards()

        if load_all or options["definitions"]:
            self._load_definitions()

        if load_all or options["rules"]:
            self._load_rules()

        if load_all or options["transformations"]:
            self._load_transformations()

        if load_all or options["analogs"]:
            self._load_analogs()

        if options["embeddings"]:
            self._generate_embeddings()

        self.stdout.write(self.style.SUCCESS("TRIZ knowledge base data loaded successfully!"))

    def _load_json(self, filename: str) -> list:
        """Load and parse a JSON fixture file."""
        filepath = FIXTURES_DIR / filename
        if not filepath.exists():
            raise CommandError(f"Fixture file not found: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data

    def _clear_data(self):
        """Clear all knowledge base data."""
        self.stdout.write("Clearing existing knowledge base data...")
        models_to_clear = [
            TypicalTransformation,
            AnalogTask,
            Rule,
            Definition,
            Standard,
            TechnologicalEffect,
            TRIZPrinciple,
        ]
        for model in models_to_clear:
            count, _ = model.objects.all().delete()
            if count:
                self.stdout.write(f"  Deleted {count} {model.__name__} records")
        self.stdout.write(self.style.SUCCESS("Data cleared."))

    @transaction.atomic
    def _load_principles(self):
        """Load 50 inventive principles and set up paired relationships."""
        self.stdout.write("Loading inventive principles...")

        data = self._load_json("principles.json")
        created_count = 0
        updated_count = 0

        for item in data:
            obj, created = TRIZPrinciple.objects.update_or_create(
                number=item["number"],
                defaults={
                    "name": item["name"],
                    "description": item["description"],
                    "examples": item.get("examples", []),
                    "is_additional": item.get("is_additional", False),
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            f"  Principles: {created_count} created, {updated_count} updated "
            f"(total: {len(data)})"
        )

        # Load paired principles
        self.stdout.write("Loading paired principles...")
        paired_data = self._load_json("paired_principles.json")
        paired_count = 0

        for pair in paired_data:
            try:
                principle = TRIZPrinciple.objects.get(number=pair["principle_number"])
                paired = TRIZPrinciple.objects.get(number=pair["paired_with_number"])
                principle.paired_with = paired
                principle.save(update_fields=["paired_with"])
                paired_count += 1
            except TRIZPrinciple.DoesNotExist:
                self.stderr.write(
                    self.style.WARNING(
                        f"  Skipping pair: principle {pair['principle_number']} "
                        f"or {pair['paired_with_number']} not found"
                    )
                )

        self.stdout.write(f"  Paired principles: {paired_count} pairs set")

    @transaction.atomic
    def _load_effects(self):
        """Load technological effects from 4 category files."""
        self.stdout.write("Loading technological effects...")
        total_created = 0
        total_updated = 0

        effect_files = [
            "effects_physical.json",
            "effects_chemical.json",
            "effects_biological.json",
            "effects_geometrical.json",
        ]

        for filename in effect_files:
            data = self._load_json(filename)
            created_count = 0
            updated_count = 0

            for item in data:
                obj, created = TechnologicalEffect.objects.update_or_create(
                    type=item["type"],
                    name=item["name"],
                    defaults={
                        "description": item["description"],
                        "function_keywords": item.get("function_keywords", []),
                    },
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

            total_created += created_count
            total_updated += updated_count
            effect_type = data[0]["type"] if data else "unknown"
            self.stdout.write(
                f"  {effect_type}: {created_count} created, {updated_count} updated"
            )

        self.stdout.write(
            f"  Effects total: {total_created} created, {total_updated} updated"
        )

    @transaction.atomic
    def _load_standards(self):
        """Load 76 TRIZ standards."""
        self.stdout.write("Loading TRIZ standards...")

        data = self._load_json("standards.json")
        created_count = 0
        updated_count = 0

        for item in data:
            obj, created = Standard.objects.update_or_create(
                number=item["number"],
                defaults={
                    "class_number": item["class_number"],
                    "name": item["name"],
                    "description": item["description"],
                    "applicability": item.get("applicability", ""),
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            f"  Standards: {created_count} created, {updated_count} updated "
            f"(total: {len(data)})"
        )

    @transaction.atomic
    def _load_definitions(self):
        """Load 35 TRIZ definitions."""
        self.stdout.write("Loading TRIZ definitions...")

        data = self._load_json("definitions.json")
        created_count = 0
        updated_count = 0

        for item in data:
            obj, created = Definition.objects.update_or_create(
                number=item["number"],
                defaults={
                    "term": item["term"],
                    "definition": item["definition"],
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            f"  Definitions: {created_count} created, {updated_count} updated "
            f"(total: {len(data)})"
        )

    @transaction.atomic
    def _load_rules(self):
        """Load 28 ARIZ rules."""
        self.stdout.write("Loading ARIZ rules...")

        data = self._load_json("rules.json")
        created_count = 0
        updated_count = 0

        for item in data:
            obj, created = Rule.objects.update_or_create(
                number=item["number"],
                defaults={
                    "name": item["name"],
                    "description": item["description"],
                    "examples": item.get("examples", []),
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            f"  Rules: {created_count} created, {updated_count} updated "
            f"(total: {len(data)})"
        )

    @transaction.atomic
    def _load_transformations(self):
        """Load typical transformations for resolving contradictions."""
        self.stdout.write("Loading typical transformations...")

        data = self._load_json("typical_transformations.json")
        created_count = 0
        updated_count = 0

        for item in data:
            obj, created = TypicalTransformation.objects.update_or_create(
                contradiction_type=item["contradiction_type"],
                transformation=item["transformation"],
                defaults={
                    "description": item["description"],
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            f"  Transformations: {created_count} created, {updated_count} updated "
            f"(total: {len(data)})"
        )

    @transaction.atomic
    def _load_analogs(self):
        """Load analog tasks from Chapter 6."""
        self.stdout.write("Loading analog tasks...")

        data = self._load_json("analog_tasks.json")
        created_count = 0
        updated_count = 0

        for item in data:
            obj, created = AnalogTask.objects.update_or_create(
                title=item["title"],
                defaults={
                    "problem_description": item["problem_description"],
                    "op_formulation": item["op_formulation"],
                    "solution_principle": item["solution_principle"],
                    "domain": item.get("domain", ""),
                    "source": item.get("source", ""),
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            f"  Analog tasks: {created_count} created, {updated_count} updated "
            f"(total: {len(data)})"
        )

    def _generate_embeddings(self):
        """Generate embeddings for effects and analog tasks using OpenAI API."""
        self.stdout.write("Generating embeddings...")

        try:
            from apps.llm_service.client import OpenAIClient
        except ImportError:
            self.stderr.write(
                self.style.WARNING(
                    "OpenAIClient not available. Skipping embedding generation. "
                    "Embeddings can be generated later with: "
                    "python manage.py load_triz_data --embeddings"
                )
            )
            return

        client = OpenAIClient()

        # Generate embeddings for effects
        effects = TechnologicalEffect.objects.filter(embedding__isnull=True)
        if effects.exists():
            self.stdout.write(f"  Generating embeddings for {effects.count()} effects...")
            for effect in effects:
                text = f"{effect.name}: {effect.description}"
                try:
                    embedding = client.create_embedding(text)
                    effect.embedding = embedding
                    effect.save(update_fields=["embedding"])
                except Exception as e:
                    logger.warning(
                        "Failed to generate embedding for effect %s: %s",
                        effect.name,
                        str(e),
                    )
                    self.stderr.write(
                        self.style.WARNING(
                            f"  Failed to generate embedding for effect: {effect.name}"
                        )
                    )
            self.stdout.write(
                self.style.SUCCESS("  Effect embeddings generated.")
            )
        else:
            self.stdout.write("  All effects already have embeddings.")

        # Generate embeddings for analog tasks
        analogs = AnalogTask.objects.filter(embedding__isnull=True)
        if analogs.exists():
            self.stdout.write(
                f"  Generating embeddings for {analogs.count()} analog tasks..."
            )
            for analog in analogs:
                text = f"{analog.title}: {analog.op_formulation}"
                try:
                    embedding = client.create_embedding(text)
                    analog.embedding = embedding
                    analog.save(update_fields=["embedding"])
                except Exception as e:
                    logger.warning(
                        "Failed to generate embedding for analog %s: %s",
                        analog.title,
                        str(e),
                    )
                    self.stderr.write(
                        self.style.WARNING(
                            f"  Failed to generate embedding for analog: {analog.title}"
                        )
                    )
            self.stdout.write(
                self.style.SUCCESS("  Analog task embeddings generated.")
            )
        else:
            self.stdout.write("  All analog tasks already have embeddings.")

        self.stdout.write(self.style.SUCCESS("Embedding generation complete."))
