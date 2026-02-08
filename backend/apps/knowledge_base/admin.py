"""
Admin registration for all TRIZ Knowledge Base models.
"""

from django.contrib import admin

from .models import (
    AnalogTask,
    Definition,
    Rule,
    Standard,
    TechnologicalEffect,
    TRIZPrinciple,
    TypicalTransformation,
)


@admin.register(TRIZPrinciple)
class TRIZPrincipleAdmin(admin.ModelAdmin):
    list_display = ("number", "name", "is_additional", "paired_with", "updated_at")
    list_filter = ("is_additional",)
    search_fields = ("name", "description")
    ordering = ("number",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(TechnologicalEffect)
class TechnologicalEffectAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "updated_at")
    list_filter = ("type",)
    search_fields = ("name", "description")
    ordering = ("type", "name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Standard)
class StandardAdmin(admin.ModelAdmin):
    list_display = ("number", "name", "class_number", "updated_at")
    list_filter = ("class_number",)
    search_fields = ("number", "name", "description")
    ordering = ("class_number", "number")
    readonly_fields = ("created_at", "updated_at")


@admin.register(AnalogTask)
class AnalogTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "domain", "source", "updated_at")
    list_filter = ("domain",)
    search_fields = ("title", "problem_description", "op_formulation")
    ordering = ("title",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Definition)
class DefinitionAdmin(admin.ModelAdmin):
    list_display = ("number", "term", "updated_at")
    search_fields = ("term", "definition")
    ordering = ("number",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ("number", "name", "updated_at")
    search_fields = ("name", "description")
    ordering = ("number",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(TypicalTransformation)
class TypicalTransformationAdmin(admin.ModelAdmin):
    list_display = ("contradiction_type", "transformation", "updated_at")
    list_filter = ("contradiction_type",)
    search_fields = ("contradiction_type", "transformation", "description")
    ordering = ("contradiction_type", "transformation")
    readonly_fields = ("created_at", "updated_at")
