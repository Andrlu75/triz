from django.conf import settings
from django.db import models


class Problem(models.Model):
    MODE_CHOICES = [
        ("express", "Express"),
        ("full", "Full"),
        ("autopilot", "Autopilot"),
    ]

    DOMAIN_CHOICES = [
        ("technical", "Technical"),
        ("business", "Business"),
        ("everyday", "Everyday"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("archived", "Archived"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="problems",
    )
    title = models.CharField(max_length=255)
    original_description = models.TextField()
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default="express")
    domain = models.CharField(max_length=10, choices=DOMAIN_CHOICES, default="technical")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="draft")
    final_report = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title


class ProblemShare(models.Model):
    PERMISSION_CHOICES = [
        ("view", "View"),
        ("comment", "Comment"),
        ("edit", "Edit"),
    ]

    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name="shares",
    )
    shared_with = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shared_problems",
    )
    permission = models.CharField(
        max_length=10, choices=PERMISSION_CHOICES, default="view"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("problem", "shared_with")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.problem.title} → {self.shared_with.username} ({self.permission})"
