"""
Billing: plan limits and middleware for enforcing them.

Plans:
    Free     — 5 problems/month, Express only
    Pro      — 50 problems/month, Express + Autopilot, reports
    Business — unlimited, all modes, teams, reports
"""
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

PLAN_LIMITS = {
    "free": {
        "problems_per_month": 5,
        "allowed_modes": ["express"],
        "reports_enabled": False,
        "teams_enabled": False,
    },
    "pro": {
        "problems_per_month": 50,
        "allowed_modes": ["express", "autopilot"],
        "reports_enabled": True,
        "teams_enabled": False,
    },
    "business": {
        "problems_per_month": None,  # unlimited
        "allowed_modes": ["express", "full", "autopilot"],
        "reports_enabled": True,
        "teams_enabled": True,
    },
}


def get_user_limits(user):
    """Return the plan limits for a given user."""
    return PLAN_LIMITS.get(user.plan, PLAN_LIMITS["free"])


def get_monthly_problem_count(user):
    """Count problems created by user in the current calendar month."""
    from apps.problems.models import Problem

    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return Problem.objects.filter(user=user, created_at__gte=month_start).count()


def check_problem_limit(user):
    """Return True if the user can still create problems this month."""
    limits = get_user_limits(user)
    max_problems = limits["problems_per_month"]
    if max_problems is None:
        return True
    return get_monthly_problem_count(user) < max_problems


def check_mode_allowed(user, mode):
    """Return True if the user's plan allows the given mode."""
    limits = get_user_limits(user)
    return mode in limits["allowed_modes"]


def check_reports_allowed(user):
    """Return True if the user's plan includes report generation."""
    return get_user_limits(user)["reports_enabled"]


def check_teams_allowed(user):
    """Return True if the user's plan includes team features."""
    return get_user_limits(user)["teams_enabled"]


class PlanLimitMiddleware:
    """
    DRF-compatible middleware that checks plan limits on problem creation
    and session start endpoints.

    Attach via Django MIDDLEWARE setting.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return None

        path = request.path

        # Check problem creation limit
        if request.method == "POST" and "/api/v1/problems/" in path and path.endswith("/"):
            if not path.endswith("/problems/"):
                return None  # skip detail actions
            if not check_problem_limit(request.user):
                return Response(
                    {
                        "detail": "Превышен лимит задач для вашего тарифа.",
                        "code": "plan_limit_exceeded",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Check mode on session start
        if request.method == "POST" and "/sessions/start/" in path:
            mode = getattr(request, "data", {}).get("mode", "express")
            if not check_mode_allowed(request.user, mode):
                return Response(
                    {
                        "detail": f'Режим "{mode}" недоступен для вашего тарифа.',
                        "code": "mode_not_allowed",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Check report generation
        if request.method == "POST" and "/reports/" in path:
            if not check_reports_allowed(request.user):
                return Response(
                    {
                        "detail": "Генерация отчётов недоступна для вашего тарифа.",
                        "code": "reports_not_allowed",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        return None
