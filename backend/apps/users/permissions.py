"""
DRF permission classes for enforcing billing plan limits.

These replace the former PlanLimitMiddleware, which could not properly
parse DRF request.data (Django HttpRequest has no .data) and returned
DRF Response objects without accepted_renderer (causing crashes in
middleware context).

Usage:
    - CanCreateProblem      — on ProblemViewSet (checks monthly quota)
    - CanUseMode            — on SessionViewSet.start (checks allowed modes)
    - CanGenerateReport     — on report download views
"""
from rest_framework.permissions import BasePermission

from apps.users.billing import (
    check_mode_allowed,
    check_problem_limit,
    check_reports_allowed,
)


class CanCreateProblem(BasePermission):
    """
    Denies POST to the problem list endpoint if the user has exceeded
    their monthly problem creation quota.

    Only applies to 'create' actions (POST on list endpoint).
    Other actions (retrieve, update, delete, share, etc.) pass through.
    """

    message = "Превышен лимит задач для вашего тарифа."
    code = "plan_limit_exceeded"

    def has_permission(self, request, view):
        # Only gate the create action
        if view.action != "create":
            return True

        if not request.user or not request.user.is_authenticated:
            return True  # let IsAuthenticated handle this

        return check_problem_limit(request.user)


class CanUseMode(BasePermission):
    """
    Denies POST to the session start endpoint if the requested ARIZ mode
    is not allowed by the user's plan.

    Only applies to the 'start' action. request.data is available because
    this runs inside a DRF APIView where the request is properly parsed.
    """

    message = "Режим недоступен для вашего тарифа."
    code = "mode_not_allowed"

    def has_permission(self, request, view):
        # Only gate the start action
        if getattr(view, "action", None) != "start":
            return True

        if not request.user or not request.user.is_authenticated:
            return True  # let IsAuthenticated handle this

        mode = request.data.get("mode", "express")
        if not check_mode_allowed(request.user, mode):
            self.message = f'Режим "{mode}" недоступен для вашего тарифа.'
            return False

        return True


class CanGenerateReport(BasePermission):
    """
    Denies access to report generation/download endpoints if the user's
    plan does not include reports.
    """

    message = "Генерация отчётов недоступна для вашего тарифа."
    code = "reports_not_allowed"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return True  # let IsAuthenticated handle this

        return check_reports_allowed(request.user)
