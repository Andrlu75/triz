"""
Models for the TRIZ Knowledge Base (Informational Fund).

Contains 50 inventive principles, technological effects, 76 standards,
analog tasks, 35 definitions, 28 ARIZ rules, and typical transformations.
"""

from django.db import models
from pgvector.django import VectorField


class TRIZPrinciple(models.Model):
    """
    Inventive principle for resolving technical contradictions.
    40 classical Altshuller principles + 10 additional (Petrov).
    """

    number = models.PositiveIntegerField(
        unique=True,
        help_text="Principle number (1-50)",
    )
    name = models.CharField(
        max_length=255,
        help_text="Short name of the principle",
    )
    description = models.TextField(
        help_text="Full description of the principle",
    )
    examples = models.JSONField(
        default=list,
        blank=True,
        help_text="List of application examples",
    )
    is_additional = models.BooleanField(
        default=False,
        help_text="True for principles 41-50 (additional by Petrov)",
    )
    paired_with = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="paired_from",
        help_text="Paired anti-principle",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["number"]
        verbose_name = "TRIZ Principle"
        verbose_name_plural = "TRIZ Principles"

    def __str__(self):
        prefix = "(доп.) " if self.is_additional else ""
        return f"{self.number}. {prefix}{self.name}"


class TechnologicalEffect(models.Model):
    """
    Technological effect from the TRIZ effects database.
    Types: physical, chemical, biological, geometrical.
    """

    EFFECT_TYPES = [
        ("physical", "Physical"),
        ("chemical", "Chemical"),
        ("biological", "Biological"),
        ("geometrical", "Geometrical"),
    ]

    type = models.CharField(
        max_length=20,
        choices=EFFECT_TYPES,
        help_text="Effect category",
    )
    name = models.CharField(
        max_length=255,
        help_text="Effect name",
    )
    description = models.TextField(
        help_text="Detailed description of the effect",
    )
    function_keywords = models.JSONField(
        default=list,
        blank=True,
        help_text="Keywords describing functions this effect can perform",
    )
    embedding = VectorField(
        dimensions=1536,
        null=True,
        blank=True,
        help_text="OpenAI text-embedding-3-small vector",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["type", "name"]
        verbose_name = "Technological Effect"
        verbose_name_plural = "Technological Effects"

    def __str__(self):
        return f"[{self.get_type_display()}] {self.name}"


class Standard(models.Model):
    """
    TRIZ Standard for solving inventive problems.
    76 standards organized in 5 classes.
    """

    class_number = models.PositiveIntegerField(
        help_text="Standard class (1-5)",
    )
    number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Full standard number, e.g. '1.1.1'",
    )
    name = models.CharField(
        max_length=255,
        help_text="Standard name",
    )
    description = models.TextField(
        help_text="Full description of the standard",
    )
    applicability = models.TextField(
        blank=True,
        default="",
        help_text="When and where this standard applies",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["class_number", "number"]
        verbose_name = "TRIZ Standard"
        verbose_name_plural = "TRIZ Standards"

    def __str__(self):
        return f"Стандарт {self.number}: {self.name}"


class AnalogTask(models.Model):
    """
    Solved analog task from TRIZ practice (Chapter 6 of Petrov's book).
    Used for vector search by OP formulation.
    """

    title = models.CharField(
        max_length=500,
        help_text="Task title",
    )
    problem_description = models.TextField(
        help_text="Full description of the original problem",
    )
    op_formulation = models.TextField(
        help_text="Sharpened Contradiction (OP) formulation",
    )
    solution_principle = models.TextField(
        help_text="Description of the solution and principle used",
    )
    domain = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Technical domain (e.g. mechanical, electrical)",
    )
    source = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Source reference (book, chapter, page)",
    )
    embedding = VectorField(
        dimensions=1536,
        null=True,
        blank=True,
        help_text="OpenAI text-embedding-3-small vector for OP formulation",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "Analog Task"
        verbose_name_plural = "Analog Tasks"

    def __str__(self):
        return self.title


class Definition(models.Model):
    """
    TRIZ definition from Appendix 4 (35 definitions).
    Terms and their definitions used in ARIZ methodology.
    """

    number = models.PositiveIntegerField(
        unique=True,
        help_text="Definition number (1-35)",
    )
    term = models.CharField(
        max_length=255,
        help_text="Term being defined",
    )
    definition = models.TextField(
        help_text="Full definition text",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["number"]
        verbose_name = "TRIZ Definition"
        verbose_name_plural = "TRIZ Definitions"

    def __str__(self):
        return f"{self.number}. {self.term}"


class Rule(models.Model):
    """
    ARIZ rule (28 rules from Petrov's book).
    Govern the ARIZ process at various steps.
    """

    number = models.PositiveIntegerField(
        unique=True,
        help_text="Rule number (1-28)",
    )
    name = models.CharField(
        max_length=255,
        help_text="Short rule name",
    )
    description = models.TextField(
        help_text="Full rule description",
    )
    examples = models.JSONField(
        default=list,
        blank=True,
        help_text="Application examples",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["number"]
        verbose_name = "ARIZ Rule"
        verbose_name_plural = "ARIZ Rules"

    def __str__(self):
        return f"Правило {self.number}: {self.name}"


class TypicalTransformation(models.Model):
    """
    Typical transformation for resolving contradictions.
    Maps contradiction types to known transformation patterns.
    """

    contradiction_type = models.CharField(
        max_length=255,
        help_text="Type of contradiction this transformation resolves",
    )
    transformation = models.CharField(
        max_length=255,
        help_text="Short name of the transformation",
    )
    description = models.TextField(
        help_text="Full description of the transformation",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["contradiction_type", "transformation"]
        verbose_name = "Typical Transformation"
        verbose_name_plural = "Typical Transformations"

    def __str__(self):
        return f"{self.contradiction_type} -> {self.transformation}"
