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

    def test_ordering_by_novelty(self, session):
        Solution.objects.create(
            session=session, method_used="principle",
            title="Low", description="D", novelty_score=3, feasibility_score=5,
        )
        Solution.objects.create(
            session=session, method_used="effect",
            title="High", description="D", novelty_score=9, feasibility_score=5,
        )
        qs = list(Solution.objects.filter(session=session))
        assert qs[0].novelty_score >= qs[-1].novelty_score


# ---------- Cross-model integration ----------


class TestCrossModelIntegration:
    """Full ARIZ session lifecycle with all related objects."""

    def test_full_session_lifecycle(self):
        org = Organization.objects.create(name="Innovators Inc.")
        user = User.objects.create_user(
            username="inventor", password="p@ss", organization=org, plan="pro",
        )
        problem = Problem.objects.create(
            user=user,
            title="Self-sharpening blade",
            original_description="The blade dulls after 10 uses.",
            mode="express",
            domain="technical",
        )
        session = ARIZSession.objects.create(problem=problem, mode="express")

        # Create all 7 express steps
        for i in range(1, 8):
            StepResult.objects.create(
                session=session,
                step_code=str(i),
                step_name=f"Express step {i}",
                user_input=f"Input for step {i}",
                llm_output=f"LLM output for step {i}",
                validated_result=f"Validated step {i}",
                status="completed",
            )

        # Create contradictions of all types
        Contradiction.objects.create(
            session=session, type="surface",
            quality_a="Sharpness", quality_b="Durability",
            formulation="The blade must be sharp but wears quickly.",
        )
        Contradiction.objects.create(
            session=session, type="deepened",
            quality_a="Hardness", quality_b="Brittleness",
            formulation="Harder material is more brittle.",
        )
        Contradiction.objects.create(
            session=session, type="sharpened",
            property_s="Hardness", anti_property_s="Elasticity",
            formulation="Material must be both hard and elastic.",
        )

        # Create IKR
        IKR.objects.create(
            session=session,
            formulation="The blade sharpens itself during use.",
            strengthened_formulation="Uses wear to create a new sharp edge.",
            vpr_used=["material_structure", "wear_pattern"],
        )

        # Create solutions
        Solution.objects.create(
            session=session, method_used="principle",
            title="Layered blade", description="Multiple hard/soft layers.",
            novelty_score=9, feasibility_score=7,
        )
        Solution.objects.create(
            session=session, method_used="effect",
            title="Self-sharpening ceramic",
            description="Ceramic that fractures along crystal planes.",
            novelty_score=8, feasibility_score=6,
        )

        # Mark session completed
        session.status = "completed"
        session.completed_at = timezone.now()
        session.context_snapshot = {
            "problem": problem.title,
            "steps_completed": 7,
            "solutions_count": 2,
        }
        session.save()

        # Verify counts
        assert session.steps.count() == 7
        assert session.contradictions.count() == 3
        assert session.ikrs.count() == 1
        assert session.solutions.count() == 2
        assert problem.sessions.count() == 1
        assert user.problems.count() == 1

        # Cascade: deleting user removes everything downstream
        session_pk = session.pk
        user.delete()
        assert Problem.objects.filter(pk=problem.pk).count() == 0
        assert ARIZSession.objects.filter(pk=session_pk).count() == 0
        assert StepResult.objects.filter(session_id=session_pk).count() == 0
        assert Contradiction.objects.filter(session_id=session_pk).count() == 0
        assert IKR.objects.filter(session_id=session_pk).count() == 0
        assert Solution.objects.filter(session_id=session_pk).count() == 0
        # Organization survives
        assert Organization.objects.filter(pk=org.pk).exists()

    def test_multiple_sessions_per_problem(self):
        user = User.objects.create_user(username="multi", password="p")
        problem = Problem.objects.create(
            user=user, title="Multi-session", original_description="D",
        )
        ARIZSession.objects.create(problem=problem, mode="express")
        ARIZSession.objects.create(problem=problem, mode="full")
        ARIZSession.objects.create(problem=problem, mode="autopilot")
        assert problem.sessions.count() == 3

    def test_final_report_json(self):
        user = User.objects.create_user(username="reporter", password="p")
        problem = Problem.objects.create(
            user=user, title="Report test", original_description="D",
        )
        problem.final_report = {
            "summary": "Heat dissipation improved by 40%",
            "solutions": [
                {"title": "Phase-change", "score": 8},
                {"title": "Heat pipes", "score": 7},
            ],
        }
        problem.save()
        problem.refresh_from_db()
        assert problem.final_report["summary"].startswith("Heat")
        assert len(problem.final_report["solutions"]) == 2

    def test_context_snapshot_json(self):
        user = User.objects.create_user(username="ctx", password="p")
        problem = Problem.objects.create(
            user=user, title="Ctx test", original_description="D",
        )
        session = ARIZSession.objects.create(problem=problem, mode="express")
        session.context_snapshot = {
            "previous_steps": [
                {"code": "1", "result": "Formulated"},
                {"code": "2", "result": "Contradiction found"},
            ],
            "current_contradiction": "Surface: A vs B",
        }
        session.save()
        session.refresh_from_db()
        assert len(session.context_snapshot["previous_steps"]) == 2

    def test_verbose_names(self):
        assert ARIZSession._meta.verbose_name == "ARIZ Session"
        assert ARIZSession._meta.verbose_name_plural == "ARIZ Sessions"
        assert IKR._meta.verbose_name == "IKR"
        assert IKR._meta.verbose_name_plural == "IKRs"

    def test_organization_ordering(self):
        org1 = Organization.objects.create(name="First")
        org2 = Organization.objects.create(name="Second")
        qs = list(Organization.objects.all())
        assert qs[0].created_at >= qs[-1].created_at

    def test_step_result_ordering(self):
        user = User.objects.create_user(username="ordtest", password="p")
        problem = Problem.objects.create(
            user=user, title="Ord", original_description="D",
        )
        session = ARIZSession.objects.create(problem=problem, mode="express")
        sr1 = StepResult.objects.create(
            session=session, step_code="1", step_name="First",
        )
        sr2 = StepResult.objects.create(
            session=session, step_code="2", step_name="Second",
        )
        qs = list(StepResult.objects.filter(session=session))
        # ordered by created_at ascending
        assert qs[0].created_at <= qs[-1].created_at
