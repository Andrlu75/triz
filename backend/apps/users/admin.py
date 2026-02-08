from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Organization, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "plan", "organization", "is_staff")
    list_filter = ("plan", "is_staff", "is_active")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("TRIZ", {"fields": ("plan", "organization", "locale")}),
    )


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)
