from django.contrib import admin

from .models import ARIZSession, Contradiction, IKR, Solution, StepResult


class StepResultInline(admin.TabularInline):
    model = StepResult
    extra = 0
    readonly_fields = ("step_code", "step_name", "status", "created_at")


class ContradictionInline(admin.TabularInline):
    model = Contradiction
    extra = 0


class SolutionInline(admin.TabularInline):
    model = Solution
    extra = 0


@admin.register(ARIZSession)
class ARIZSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "problem", "mode", "current_step", "status", "created_at")
    list_filter = ("mode", "status")
    raw_id_fields = ("problem",)
    inlines = [StepResultInline, ContradictionInline, SolutionInline]


@admin.register(StepResult)
class StepResultAdmin(admin.ModelAdmin):
    list_display = ("session", "step_code", "step_name", "status", "created_at")
    list_filter = ("status",)
    raw_id_fields = ("session",)


@admin.register(Contradiction)
class ContradictionAdmin(admin.ModelAdmin):
    list_display = ("session", "type", "formulation")
    list_filter = ("type",)
    raw_id_fields = ("session",)


@admin.register(IKR)
class IKRAdmin(admin.ModelAdmin):
    list_display = ("session", "formulation")
    raw_id_fields = ("session",)


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    list_display = ("title", "session", "method_used", "novelty_score", "feasibility_score")
    list_filter = ("method_used",)
    raw_id_fields = ("session",)
