from django.contrib import admin

from .models import GeneratedReport


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "session",
        "format",
        "status",
        "file_size",
        "created_at",
        "completed_at",
    ]
    list_filter = ["format", "status"]
    search_fields = ["session__problem__title"]
    readonly_fields = ["id", "created_at", "completed_at"]
