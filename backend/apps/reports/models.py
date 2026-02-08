import uuid

from django.conf import settings
from django.db import models

from apps.ariz_engine.models import ARIZSession


class GeneratedReport(models.Model):
    """Stores metadata and file path for generated PDF/DOCX reports."""

    FORMAT_CHOICES = [
        ("pdf", "PDF"),
        ("docx", "DOCX"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("generating", "Generating"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ARIZSession,
        on_delete=models.CASCADE,
        related_name="reports",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="requested_reports",
    )
    format = models.CharField(max_length=4, choices=FORMAT_CHOICES)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="pending"
    )
    file_path = models.CharField(max_length=512, blank=True, default="")
    file_size = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Generated Report"
        verbose_name_plural = "Generated Reports"

    def __str__(self):
        return (
            f"Report {self.id} — {self.session.problem.title} "
            f"({self.format.upper()})"
        )

    @property
    def filename(self):
        """Generate a human-readable filename for download."""
        safe_title = "".join(
            c if c.isalnum() or c in (" ", "-", "_") else "_"
            for c in self.session.problem.title
        )[:80].strip()
        return f"TRIZ_Report_{safe_title}.{self.format}"
