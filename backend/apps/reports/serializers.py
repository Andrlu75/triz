from rest_framework import serializers

from .models import GeneratedReport


class GeneratedReportSerializer(serializers.ModelSerializer):
    """Serializer for GeneratedReport model."""

    filename = serializers.CharField(read_only=True)
    session_id = serializers.IntegerField(source="session.id", read_only=True)
    problem_title = serializers.CharField(
        source="session.problem.title", read_only=True
    )

    class Meta:
        model = GeneratedReport
        fields = [
            "id",
            "session_id",
            "problem_title",
            "format",
            "status",
            "filename",
            "file_size",
            "error_message",
            "created_at",
            "completed_at",
        ]
        read_only_fields = fields


class ReportRequestSerializer(serializers.Serializer):
    """Serializer for requesting report generation."""

    format = serializers.ChoiceField(choices=["pdf", "docx"])
