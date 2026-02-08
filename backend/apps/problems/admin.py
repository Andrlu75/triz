from django.contrib import admin

from .models import Problem


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "mode", "domain", "status", "created_at")
    list_filter = ("mode", "domain", "status")
    search_fields = ("title", "original_description")
    raw_id_fields = ("user",)
