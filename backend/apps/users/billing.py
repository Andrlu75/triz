"""
Billing: plan limits and utility functions for enforcing them.

Plans:
    Free     — 5 problems/month, Express only
    Pro      — 50 problems/month, Express + Autopilot, reports
    Business — unlimited, all modes, teams, reports

Note: Enforcement is handled by DRF permission classes in
``apps.users.permissions`` (CanCreateProblem, CanUseMode, CanGenerateReport).
"""
from django.utils import timezone

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
