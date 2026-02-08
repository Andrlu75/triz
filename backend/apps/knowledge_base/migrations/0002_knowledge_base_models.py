"""
Migration creating all knowledge base models:
TRIZPrinciple, TechnologicalEffect, Standard, AnalogTask,
Definition, Rule, TypicalTransformation.
"""

import django.db.models.deletion
import pgvector.django
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("knowledge_base", "0001_create_vector_extension"),
    ]

    operations = [
        migrations.CreateModel(
            name="TRIZPrinciple",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "number",
                    models.PositiveIntegerField(
                        help_text="Principle number (1-50)",
                        unique=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Short name of the principle",
                        max_length=255,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        help_text="Full description of the principle",
                    ),
                ),
                (
                    "examples",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="List of application examples",
                    ),
                ),
                (
                    "is_additional",
                    models.BooleanField(
                        default=False,
                        help_text="True for principles 41-50 (additional by Petrov)",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
                (
                    "paired_with",
                    models.ForeignKey(
                        blank=True,
                        help_text="Paired anti-principle",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="paired_from",
                        to="knowledge_base.trizprinciple",
                    ),
                ),
            ],
            options={
                "verbose_name": "TRIZ Principle",
                "verbose_name_plural": "TRIZ Principles",
                "ordering": ["number"],
            },
        ),
        migrations.CreateModel(
            name="TechnologicalEffect",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("physical", "Physical"),
                            ("chemical", "Chemical"),
                            ("biological", "Biological"),
                            ("geometrical", "Geometrical"),
                        ],
                        help_text="Effect category",
                        max_length=20,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Effect name",
                        max_length=255,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        help_text="Detailed description of the effect",
                    ),
                ),
                (
                    "function_keywords",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="Keywords describing functions this effect can perform",
                    ),
                ),
                (
                    "embedding",
                    pgvector.django.VectorField(
                        blank=True,
                        dimensions=1536,
                        help_text="OpenAI text-embedding-3-small vector",
                        null=True,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
            ],
            options={
                "verbose_name": "Technological Effect",
                "verbose_name_plural": "Technological Effects",
                "ordering": ["type", "name"],
            },
        ),
        migrations.CreateModel(
            name="Standard",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "class_number",
                    models.PositiveIntegerField(
                        help_text="Standard class (1-5)",
                    ),
                ),
                (
                    "number",
                    models.CharField(
                        help_text="Full standard number, e.g. '1.1.1'",
                        max_length=20,
                        unique=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Standard name",
                        max_length=255,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        help_text="Full description of the standard",
                    ),
                ),
                (
                    "applicability",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="When and where this standard applies",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
            ],
            options={
                "verbose_name": "TRIZ Standard",
                "verbose_name_plural": "TRIZ Standards",
                "ordering": ["class_number", "number"],
            },
        ),
        migrations.CreateModel(
            name="AnalogTask",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "title",
                    models.CharField(
                        help_text="Task title",
                        max_length=500,
                    ),
                ),
                (
                    "problem_description",
                    models.TextField(
                        help_text="Full description of the original problem",
                    ),
                ),
                (
                    "op_formulation",
                    models.TextField(
                        help_text="Sharpened Contradiction (OP) formulation",
                    ),
                ),
                (
                    "solution_principle",
                    models.TextField(
                        help_text="Description of the solution and principle used",
                    ),
                ),
                (
                    "domain",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Technical domain (e.g. mechanical, electrical)",
                        max_length=100,
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Source reference (book, chapter, page)",
                        max_length=255,
                    ),
                ),
                (
                    "embedding",
                    pgvector.django.VectorField(
                        blank=True,
                        dimensions=1536,
                        help_text="OpenAI text-embedding-3-small vector for OP formulation",
                        null=True,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
            ],
            options={
                "verbose_name": "Analog Task",
                "verbose_name_plural": "Analog Tasks",
                "ordering": ["title"],
            },
        ),
        migrations.CreateModel(
            name="Definition",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "number",
                    models.PositiveIntegerField(
                        help_text="Definition number (1-35)",
                        unique=True,
                    ),
                ),
                (
                    "term",
                    models.CharField(
                        help_text="Term being defined",
                        max_length=255,
                    ),
                ),
                (
                    "definition",
                    models.TextField(
                        help_text="Full definition text",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
            ],
            options={
                "verbose_name": "TRIZ Definition",
                "verbose_name_plural": "TRIZ Definitions",
                "ordering": ["number"],
            },
        ),
        migrations.CreateModel(
            name="Rule",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "number",
                    models.PositiveIntegerField(
                        help_text="Rule number (1-28)",
                        unique=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Short rule name",
                        max_length=255,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        help_text="Full rule description",
                    ),
                ),
                (
                    "examples",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="Application examples",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
            ],
            options={
                "verbose_name": "ARIZ Rule",
                "verbose_name_plural": "ARIZ Rules",
                "ordering": ["number"],
            },
        ),
        migrations.CreateModel(
            name="TypicalTransformation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "contradiction_type",
                    models.CharField(
                        help_text="Type of contradiction this transformation resolves",
                        max_length=255,
                    ),
                ),
                (
                    "transformation",
                    models.CharField(
                        help_text="Short name of the transformation",
                        max_length=255,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        help_text="Full description of the transformation",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
            ],
            options={
                "verbose_name": "Typical Transformation",
                "verbose_name_plural": "Typical Transformations",
                "ordering": ["contradiction_type", "transformation"],
            },
        ),
    ]
