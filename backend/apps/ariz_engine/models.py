from django.db import models

from apps.problems.models import Problem


class ARIZSession(models.Model):
    MODE_CHOICES = [
        ("express", "Express"),
        ("full", "Full"),
        ("autopilot", "Autopilot"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("abandoned", "Abandoned"),
    ]

    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    mode = models.CharField(max_length=10, choices=MODE_CHOICES)
    current_step = models.CharField(max_length=10, default="1")
    current_part = models.IntegerField(default=1)
    context_snapshot = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "ARIZ Session"
        verbose_name_plural = "ARIZ Sessions"

    def __str__(self):
        return f"Session #{self.pk} — {self.problem.title} ({self.mode})"


class StepResult(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    session = models.ForeignKey(
        ARIZSession,
        on_delete=models.CASCADE,
        related_name="steps",
    )
    step_code = models.CharField(max_length=10)
    step_name = models.CharField(max_length=255)
    user_input = models.TextField(blank=True, default="")
    llm_output = models.TextField(blank=True, default="")
    validated_result = models.TextField(blank=True, default="")
    validation_notes = models.TextField(blank=True, default="")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        unique_together = [("session", "step_code")]

    def __str__(self):
        return f"Step {self.step_code}: {self.step_name}"


class Contradiction(models.Model):
    TYPE_CHOICES = [
        ("surface", "Surface"),
        ("deepened", "Deepened"),
        ("sharpened", "Sharpened"),
    ]

    session = models.ForeignKey(
        ARIZSession,
        on_delete=models.CASCADE,
        related_name="contradictions",
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    quality_a = models.CharField(max_length=255, blank=True, default="")
    quality_b = models.CharField(max_length=255, blank=True, default="")
    property_s = models.CharField(max_length=255, blank=True, default="")
    anti_property_s = models.CharField(max_length=255, blank=True, default="")
    formulation = models.TextField()

    class Meta:
        ordering = ["type"]

    def __str__(self):
        return f"{self.get_type_display()} contradiction: {self.formulation[:60]}"


class IKR(models.Model):
    session = models.ForeignKey(
        ARIZSession,
        on_delete=models.CASCADE,
        related_name="ikrs",
    )
    formulation = models.TextField()
    strengthened_formulation = models.TextField(blank=True, default="")
    vpr_used = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name = "IKR"
        verbose_name_plural = "IKRs"

    def __str__(self):
        return f"IKR: {self.formulation[:60]}"


class Solution(models.Model):
    METHOD_CHOICES = [
        ("principle", "Principle"),
        ("standard", "Standard"),
        ("effect", "Effect"),
        ("analog", "Analog"),
        ("combined", "Combined"),
    ]

    session = models.ForeignKey(
        ARIZSession,
        on_delete=models.CASCADE,
        related_name="solutions",
    )
    method_used = models.CharField(max_length=10, choices=METHOD_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    novelty_score = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 11)],
    )
    feasibility_score = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 11)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-novelty_score"]

    def __str__(self):
        return self.title
