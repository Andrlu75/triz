import pytest
from django.utils import timezone

from apps.ariz_engine.models import (
    ARIZSession,
    Contradiction,
    IKR,
    Solution,
    StepResult,
)
from apps.problems.models import Problem
from apps.users.models import Organization, User

pytestmark = pytest.mark.django_db


# ---------- Organization ----------


class TestOrganization:
    def test_create(self):
        org = Organization.objects.create(name="ACME Corp")
        assert org.pk is not None
        assert org.name == "ACME Corp"
        assert org.created_at is not None

    def test_str(self):
        org = Organization(name="ACME Corp")
        assert str(org) == "ACME Corp"


# ---------- User ----------


class TestUser:
    def test_create_user(self):
        user = User.objects.create_user(
            username="ivan",
            email="ivan@example.com",
            password="testpass123",
        )
        assert user.pk is not None
        assert user.plan == "free"
        assert user.locale == "ru"
        assert user.organization is None

    def test_plan_choices(self):
        user = User.objects.create_user(username="pro_user", password="testpass123")
        user.plan = "pro"
        user.save()
        user.refresh_from_db()
        assert user.plan == "pro"

    def test_with_organization(self):
        org = Organization.objects.create(name="ACME Corp")
        user = User.objects.create_user(username="member", password="testpass123")
        user.organization = org
        user.save()
        user.refresh_from_db()
        assert user.organization == org
        assert org.members.count() == 1

    def test_str(self):
        user = User(username="ivan")
        assert str(user) == "ivan"


# ---------- Problem ----------


class TestProblem:
    @pytest.fixture()
    def user(self):
        return User.objects.create_user(username="solver", password="testpass123")

    def test_create(self, user):
        problem = Problem.objects.create(
            user=user,
            title="Heating issue",
            original_description="The pipe overheats during operation.",
        )
        assert problem.pk is not None
        assert problem.mode == "express"
        assert problem.domain == "technical"
        assert problem.status == "draft"
        assert problem.final_report == {}

    def test_mode_choices(self, user):
        for mode in ("express", "full", "autopilot"):
            p = Problem.objects.create(
                user=user,
                title=f"Problem {mode}",
                original_description="desc",
                mode=mode,
            )
            assert p.mode == mode

    def test_domain_choices(self, user):
        for domain in ("technical", "business", "everyday"):
            p = Problem.objects.create(
                user=user,
                title=f"Problem {domain}",
                original_description="desc",
                domain=domain,
            )
            assert p.domain == domain

    def test_user_cascade_delete(self, user):
        Problem.objects.create(user=user, title="T", original_description="D")
        assert Problem.objects.count() == 1
        user.delete()
        assert Problem.objects.count() == 0

    def test_str(self, user):
        problem = Problem(title="Test Problem")
        assert str(problem) == "Test Problem"


# ---------- ARIZSession ----------


class TestARIZSession:
    @pytest.fixture()
    def problem(self):
        user = User.objects.create_user(username="s", password="p")
        return Problem.objects.create(
            user=user, title="T", original_description="D"
        )

    def test_create(self, problem):
        session = ARIZSession.objects.create(problem=problem, mode="express")
        assert session.pk is not None
        assert session.current_step == "1"
        assert session.current_part == 1
        assert session.context_snapshot == {}
        assert session.status == "active"
        assert session.completed_at is None

    def test_complete(self, problem):
        session = ARIZSession.objects.create(problem=problem, mode="full")
        session.status = "completed"
        session.completed_at = timezone.now()
        session.save()
        session.refresh_from_db()
        assert session.status == "completed"
        assert session.completed_at is not None

    def test_str(self, problem):
        session = ARIZSession.objects.create(problem=problem, mode="express")
        assert "express" in str(session).lower()

    def test_problem_cascade(self, problem):
        ARIZSession.objects.create(problem=problem, mode="express")
        assert ARIZSession.objects.count() == 1
        problem.delete()
        assert ARIZSession.objects.count() == 0


# ---------- StepResult ----------


class TestStepResult:
    @pytest.fixture()
    def session(self):
        user = User.objects.create_user(username="s", password="p")
        problem = Problem.objects.create(user=user, title="T", original_description="D")
        return ARIZSession.objects.create(problem=problem, mode="express")

    def test_create(self, session):
        step = StepResult.objects.create(
            session=session,
            step_code="1",
            step_name="Problem formulation",
            user_input="My pipe overheats.",
            llm_output="Analyzed output...",
            validated_result="Validated result...",
            status="completed",
        )
        assert step.pk is not None
        assert step.step_code == "1"

    def test_unique_step_per_session(self, session):
        StepResult.objects.create(session=session, step_code="1", step_name="Step 1")
        with pytest.raises(Exception):
            StepResult.objects.create(session=session, step_code="1", step_name="Dup")

    def test_str(self, session):
        step = StepResult(step_code="2", step_name="Surface contradiction")
        assert "2" in str(step)

    def test_session_cascade(self, session):
        StepResult.objects.create(session=session, step_code="1", step_name="S1")
        assert StepResult.objects.count() == 1
        session.delete()
        assert StepResult.objects.count() == 0


# ---------- Contradiction ----------


class TestContradiction:
    @pytest.fixture()
    def session(self):
        user = User.objects.create_user(username="s2", password="p")
        problem = Problem.objects.create(user=user, title="T", original_description="D")
        return ARIZSession.objects.create(problem=problem, mode="express")

    def test_create(self, session):
        c = Contradiction.objects.create(
            session=session,
            type="surface",
            quality_a="Temperature",
            quality_b="Durability",
            formulation="If we increase temperature, durability decreases.",
        )
        assert c.pk is not None
        assert c.type == "surface"

    def test_type_choices(self, session):
        for t in ("surface", "deepened", "sharpened"):
            c = Contradiction.objects.create(
                session=session, type=t, formulation=f"Contradiction {t}"
            )
            assert c.type == t

    def test_str(self, session):
        c = Contradiction(type="surface", formulation="Test formulation text here")
        assert "surface" in str(c).lower()


# ---------- IKR ----------


class TestIKR:
    @pytest.fixture()
    def session(self):
        user = User.objects.create_user(username="s3", password="p")
        problem = Problem.objects.create(user=user, title="T", original_description="D")
        return ARIZSession.objects.create(problem=problem, mode="express")

    def test_create(self, session):
        ikr = IKR.objects.create(
            session=session,
            formulation="The pipe itself maintains optimal temperature.",
        )
        assert ikr.pk is not None
        assert ikr.vpr_used == []

    def test_with_strengthened(self, session):
        ikr = IKR.objects.create(
            session=session,
            formulation="Base IKR",
            strengthened_formulation="Strengthened IKR",
            vpr_used=["thermal_expansion", "phase_transition"],
        )
        assert ikr.strengthened_formulation == "Strengthened IKR"
        assert len(ikr.vpr_used) == 2

    def test_str(self, session):
        ikr = IKR(formulation="Test IKR formulation")
        assert "IKR" in str(ikr)


# ---------- Solution ----------


class TestSolution:
    @pytest.fixture()
    def session(self):
        user = User.objects.create_user(username="s4", password="p")
        problem = Problem.objects.create(user=user, title="T", original_description="D")
        return ARIZSession.objects.create(problem=problem, mode="express")

    def test_create(self, session):
        sol = Solution.objects.create(
            session=session,
            method_used="principle",
            title="Use bimetallic strip",
            description="Apply principle #35 (parameter changes).",
            novelty_score=7,
            feasibility_score=8,
        )
        assert sol.pk is not None
        assert sol.novelty_score == 7
        assert sol.feasibility_score == 8

    def test_method_choices(self, session):
        for method in ("principle", "standard", "effect", "analog", "combined"):
            sol = Solution.objects.create(
                session=session,
                method_used=method,
                title=f"Solution {method}",
                description="Desc",
                novelty_score=5,
                feasibility_score=5,
            )
            assert sol.method_used == method

    def test_str(self, session):
        sol = Solution(title="Bimetallic strip solution")
        assert str(sol) == "Bimetallic strip solution"

    def test_session_cascade(self, session):
        Solution.objects.create(
            session=session,
            method_used="principle",
            title="T",
            description="D",
            novelty_score=5,
            feasibility_score=5,
        )
        assert Solution.objects.count() == 1
        session.delete()
        assert Solution.objects.count() == 0
