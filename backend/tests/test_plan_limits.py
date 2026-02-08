"""
Tests for billing plan limits.

Covers:
    - Free plan: 5 problems/month, Express only
    - Pro plan: 50 problems/month, Express + Autopilot, reports
    - Business plan: unlimited, all modes, teams, reports
"""
from datetime import timedelta
from unittest.mock import patch

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
