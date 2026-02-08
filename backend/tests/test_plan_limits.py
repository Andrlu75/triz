"""
Tests for billing plan limits.

Covers:
    - Free plan: 5 problems/month, Express only
    - Pro plan: 50 problems/month, Express + Autopilot, reports
    - Business plan: unlimited, all modes, teams, reports
    - DRF permission classes: CanCreateProblem, CanUseMode, CanGenerateReport
"""
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from apps.users.billing import (
    PLAN_LIMITS,
    check_mode_allowed,
    check_problem_limit,
    check_reports_allowed,
    check_teams_allowed,
    get_monthly_problem_count,
    get_user_limits,
)
from apps.users.models import User
from apps.users.permissions import CanCreateProblem, CanGenerateReport, CanUseMode
from apps.problems.models import Problem


class TestPlanLimits(TestCase):
    """Test plan limit configuration."""

    def test_free_plan_limits(self):
        limits = PLAN_LIMITS["free"]
        self.assertEqual(limits["problems_per_month"], 5)
        self.assertEqual(limits["allowed_modes"], ["express"])
        self.assertFalse(limits["reports_enabled"])
        self.assertFalse(limits["teams_enabled"])

    def test_pro_plan_limits(self):
        limits = PLAN_LIMITS["pro"]
        self.assertEqual(limits["problems_per_month"], 50)
        self.assertIn("express", limits["allowed_modes"])
        self.assertIn("autopilot", limits["allowed_modes"])
        self.assertTrue(limits["reports_enabled"])
        self.assertFalse(limits["teams_enabled"])

    def test_business_plan_limits(self):
        limits = PLAN_LIMITS["business"]
        self.assertIsNone(limits["problems_per_month"])
        self.assertIn("full", limits["allowed_modes"])
        self.assertTrue(limits["reports_enabled"])
        self.assertTrue(limits["teams_enabled"])


class TestCheckModeAllowed(TestCase):
    """Test mode permission checks."""

    def setUp(self):
        self.free_user = User.objects.create_user(
            username="free_user", password="test12345678", plan="free"
        )
        self.pro_user = User.objects.create_user(
            username="pro_user", password="test12345678", plan="pro"
        )
        self.biz_user = User.objects.create_user(
            username="biz_user", password="test12345678", plan="business"
        )

    def test_free_can_use_express(self):
        self.assertTrue(check_mode_allowed(self.free_user, "express"))

    def test_free_cannot_use_full(self):
        self.assertFalse(check_mode_allowed(self.free_user, "full"))

    def test_free_cannot_use_autopilot(self):
        self.assertFalse(check_mode_allowed(self.free_user, "autopilot"))

    def test_pro_can_use_autopilot(self):
        self.assertTrue(check_mode_allowed(self.pro_user, "autopilot"))

    def test_pro_cannot_use_full(self):
        self.assertFalse(check_mode_allowed(self.pro_user, "full"))

    def test_business_can_use_all_modes(self):
        for mode in ["express", "full", "autopilot"]:
            self.assertTrue(check_mode_allowed(self.biz_user, mode))


class TestCheckProblemLimit(TestCase):
    """Test monthly problem count limits."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="limit_user", password="test12345678", plan="free"
        )

    def test_free_under_limit(self):
        for i in range(4):
            Problem.objects.create(
                user=self.user,
                title=f"Problem {i}",
                original_description="Desc",
            )
        self.assertTrue(check_problem_limit(self.user))

    def test_free_at_limit(self):
        for i in range(5):
            Problem.objects.create(
                user=self.user,
                title=f"Problem {i}",
                original_description="Desc",
            )
        self.assertFalse(check_problem_limit(self.user))

    def test_business_unlimited(self):
        self.user.plan = "business"
        self.user.save()
        for i in range(100):
            Problem.objects.create(
                user=self.user,
                title=f"Problem {i}",
                original_description="Desc",
            )
        self.assertTrue(check_problem_limit(self.user))

    def test_monthly_count(self):
        count = get_monthly_problem_count(self.user)
        self.assertEqual(count, 0)
        Problem.objects.create(
            user=self.user,
            title="New",
            original_description="Desc",
        )
        self.assertEqual(get_monthly_problem_count(self.user), 1)


class TestCheckReportsAndTeams(TestCase):
    """Test reports and teams permission checks."""

    def setUp(self):
        self.free_user = User.objects.create_user(
            username="free2", password="test12345678", plan="free"
        )
        self.pro_user = User.objects.create_user(
            username="pro2", password="test12345678", plan="pro"
        )
        self.biz_user = User.objects.create_user(
            username="biz2", password="test12345678", plan="business"
        )

    def test_free_no_reports(self):
        self.assertFalse(check_reports_allowed(self.free_user))

    def test_pro_has_reports(self):
        self.assertTrue(check_reports_allowed(self.pro_user))

    def test_free_no_teams(self):
        self.assertFalse(check_teams_allowed(self.free_user))

    def test_business_has_teams(self):
        self.assertTrue(check_teams_allowed(self.biz_user))

    def test_get_user_limits_defaults_to_free(self):
        self.free_user.plan = "unknown"
        limits = get_user_limits(self.free_user)
        self.assertEqual(limits["problems_per_month"], 5)


# -----------------------------------------------------------------------
# DRF Permission classes
# -----------------------------------------------------------------------

def _make_request(user, data=None):
    """Create a minimal mock DRF request."""
    request = MagicMock()
    request.user = user
    request.data = data or {}
    return request


def _make_view(action):
    """Create a minimal mock DRF view with the given action."""
    view = MagicMock()
    view.action = action
    return view


class TestCanCreateProblemPermission(TestCase):
    """Test the CanCreateProblem DRF permission class."""

    def setUp(self):
        self.perm = CanCreateProblem()
        self.user = User.objects.create_user(
            username="perm_user", password="test12345678", plan="free"
        )

    def test_allows_non_create_actions(self):
        """Non-create actions (list, retrieve, update) should always pass."""
        request = _make_request(self.user)
        for action in ["list", "retrieve", "partial_update", "destroy", "share"]:
            view = _make_view(action)
            self.assertTrue(self.perm.has_permission(request, view))

    def test_allows_create_under_limit(self):
        """Create is allowed when user is under monthly limit."""
        request = _make_request(self.user)
        view = _make_view("create")
        self.assertTrue(self.perm.has_permission(request, view))

    def test_denies_create_at_limit(self):
        """Create is denied when user has reached monthly limit."""
        for i in range(5):
            Problem.objects.create(
                user=self.user,
                title=f"Problem {i}",
                original_description="Desc",
            )
        request = _make_request(self.user)
        view = _make_view("create")
        self.assertFalse(self.perm.has_permission(request, view))

    def test_allows_create_business_unlimited(self):
        """Business plan users can create unlimited problems."""
        self.user.plan = "business"
        self.user.save()
        for i in range(100):
            Problem.objects.create(
                user=self.user,
                title=f"Problem {i}",
                original_description="Desc",
            )
        request = _make_request(self.user)
        view = _make_view("create")
        self.assertTrue(self.perm.has_permission(request, view))

    def test_passes_through_for_unauthenticated(self):
        """Unauthenticated users pass through (IsAuthenticated handles them)."""
        request = MagicMock()
        request.user = MagicMock()
        request.user.is_authenticated = False
        view = _make_view("create")
        self.assertTrue(self.perm.has_permission(request, view))


class TestCanUseModePermission(TestCase):
    """Test the CanUseMode DRF permission class."""

    def setUp(self):
        self.perm = CanUseMode()
        self.free_user = User.objects.create_user(
            username="mode_free", password="test12345678", plan="free"
        )
        self.pro_user = User.objects.create_user(
            username="mode_pro", password="test12345678", plan="pro"
        )
        self.biz_user = User.objects.create_user(
            username="mode_biz", password="test12345678", plan="business"
        )

    def test_allows_non_start_actions(self):
        """Non-start actions should always pass."""
        request = _make_request(self.free_user, {"mode": "full"})
        for action in ["list", "retrieve", "submit", "advance", "back"]:
            view = _make_view(action)
            self.assertTrue(self.perm.has_permission(request, view))

    def test_free_allowed_express(self):
        """Free plan allows express mode."""
        request = _make_request(self.free_user, {"mode": "express"})
        view = _make_view("start")
        self.assertTrue(self.perm.has_permission(request, view))

    def test_free_denied_full(self):
        """Free plan denies full mode."""
        request = _make_request(self.free_user, {"mode": "full"})
        view = _make_view("start")
        self.assertFalse(self.perm.has_permission(request, view))

    def test_free_denied_autopilot(self):
        """Free plan denies autopilot mode."""
        request = _make_request(self.free_user, {"mode": "autopilot"})
        view = _make_view("start")
        self.assertFalse(self.perm.has_permission(request, view))

    def test_pro_allowed_autopilot(self):
        """Pro plan allows autopilot mode."""
        request = _make_request(self.pro_user, {"mode": "autopilot"})
        view = _make_view("start")
        self.assertTrue(self.perm.has_permission(request, view))

    def test_pro_denied_full(self):
        """Pro plan denies full mode."""
        request = _make_request(self.pro_user, {"mode": "full"})
        view = _make_view("start")
        self.assertFalse(self.perm.has_permission(request, view))

    def test_business_allowed_all(self):
        """Business plan allows all modes."""
        for mode in ["express", "full", "autopilot"]:
            request = _make_request(self.biz_user, {"mode": mode})
            view = _make_view("start")
            self.assertTrue(self.perm.has_permission(request, view))

    def test_defaults_to_express_when_mode_missing(self):
        """If mode is not in request.data, defaults to 'express'."""
        request = _make_request(self.free_user, {})
        view = _make_view("start")
        self.assertTrue(self.perm.has_permission(request, view))

    def test_reads_mode_from_request_data(self):
        """Verifies that mode is read from request.data (DRF parsed data)."""
        request = _make_request(self.free_user, {"mode": "full"})
        view = _make_view("start")
        # This would have been broken in the old middleware, because
        # Django HttpRequest has no .data attribute. With the DRF
        # permission class, request.data is properly available.
        self.assertFalse(self.perm.has_permission(request, view))

    def test_passes_through_for_unauthenticated(self):
        """Unauthenticated users pass through (IsAuthenticated handles them)."""
        request = MagicMock()
        request.user = MagicMock()
        request.user.is_authenticated = False
        request.data = {"mode": "full"}
        view = _make_view("start")
        self.assertTrue(self.perm.has_permission(request, view))


class TestCanGenerateReportPermission(TestCase):
    """Test the CanGenerateReport DRF permission class."""

    def setUp(self):
        self.perm = CanGenerateReport()
        self.free_user = User.objects.create_user(
            username="rep_free", password="test12345678", plan="free"
        )
        self.pro_user = User.objects.create_user(
            username="rep_pro", password="test12345678", plan="pro"
        )
        self.biz_user = User.objects.create_user(
            username="rep_biz", password="test12345678", plan="business"
        )

    def test_free_denied(self):
        """Free plan users cannot generate reports."""
        request = _make_request(self.free_user)
        view = _make_view("get")
        self.assertFalse(self.perm.has_permission(request, view))

    def test_pro_allowed(self):
        """Pro plan users can generate reports."""
        request = _make_request(self.pro_user)
        view = _make_view("get")
        self.assertTrue(self.perm.has_permission(request, view))

    def test_business_allowed(self):
        """Business plan users can generate reports."""
        request = _make_request(self.biz_user)
        view = _make_view("get")
        self.assertTrue(self.perm.has_permission(request, view))

    def test_passes_through_for_unauthenticated(self):
        """Unauthenticated users pass through (IsAuthenticated handles them)."""
        request = MagicMock()
        request.user = MagicMock()
        request.user.is_authenticated = False
        view = _make_view("get")
        self.assertTrue(self.perm.has_permission(request, view))
