"""
Tests for #65 subtask 4.18 — authorization & input validation fixes.

Covers:
  1. OrganizationViewSet.members() POST — only admins can add members
  2. OrganizationViewSet.remove_member() — only admins can remove members
  3. OrganizationViewSet.members() POST — role validated via serializer
  4. ProblemViewSet.share() — permission validated via serializer
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.problems.models import Problem, ProblemShare
from apps.users.models import Organization, OrganizationMembership, User

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def api_client():
    return APIClient()


@pytest.fixture()
def admin_user():
    return User.objects.create_user(
        username="orgadmin", email="admin@example.com", password="testpass123"
    )


@pytest.fixture()
def member_user():
    return User.objects.create_user(
        username="orgmember", email="member@example.com", password="testpass123"
    )


@pytest.fixture()
def outsider_user():
    return User.objects.create_user(
        username="outsider", email="outsider@example.com", password="testpass123"
    )


@pytest.fixture()
def target_user():
    return User.objects.create_user(
        username="target", email="target@example.com", password="testpass123"
    )


@pytest.fixture()
def organization(admin_user, member_user):
    org = Organization.objects.create(name="Test Org")
    OrganizationMembership.objects.create(
        user=admin_user, organization=org, role="admin"
    )
    OrganizationMembership.objects.create(
        user=member_user, organization=org, role="member"
    )
    return org


@pytest.fixture()
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture()
def member_client(api_client, member_user):
    api_client.force_authenticate(user=member_user)
    return api_client


# ---------------------------------------------------------------------------
# OrganizationViewSet — admin check on members POST
# ---------------------------------------------------------------------------


class TestOrgMembersAdminCheck:
    """Only admins can add members via POST /organizations/{id}/members/."""

    def test_admin_can_add_member(self, admin_client, organization, target_user):
        url = f"/api/v1/auth/organizations/{organization.pk}/members/"
        resp = admin_client.post(url, {"username": "target", "role": "member"})
        assert resp.status_code == status.HTTP_201_CREATED
        assert OrganizationMembership.objects.filter(
            user=target_user, organization=organization
        ).exists()

    def test_member_cannot_add_member(self, member_client, organization, target_user):
        url = f"/api/v1/auth/organizations/{organization.pk}/members/"
        resp = member_client.post(url, {"username": "target", "role": "member"})
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert not OrganizationMembership.objects.filter(
            user=target_user, organization=organization
        ).exists()

    def test_get_members_allowed_for_any_member(
        self, member_client, organization
    ):
        url = f"/api/v1/auth/organizations/{organization.pk}/members/"
        resp = member_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) == 2  # admin + member


# ---------------------------------------------------------------------------
# OrganizationViewSet — admin check on remove_member
# ---------------------------------------------------------------------------


class TestOrgRemoveMemberAdminCheck:
    """Only admins can remove members via DELETE /organizations/{id}/members/{user_id}/."""

    def test_admin_can_remove_member(
        self, admin_client, organization, member_user
    ):
        url = f"/api/v1/auth/organizations/{organization.pk}/members/{member_user.pk}/"
        resp = admin_client.delete(url)
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not OrganizationMembership.objects.filter(
            user=member_user, organization=organization
        ).exists()

    def test_member_cannot_remove_member(
        self, member_client, organization, admin_user
    ):
        url = f"/api/v1/auth/organizations/{organization.pk}/members/{admin_user.pk}/"
        resp = member_client.delete(url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        # Admin membership should still exist
        assert OrganizationMembership.objects.filter(
            user=admin_user, organization=organization
        ).exists()


# ---------------------------------------------------------------------------
# OrganizationViewSet — role validation via serializer
# ---------------------------------------------------------------------------


class TestOrgMemberRoleValidation:
    """The 'role' field must be one of ROLE_CHOICES (admin, member, viewer)."""

    def test_valid_role_accepted(self, admin_client, organization, target_user):
        url = f"/api/v1/auth/organizations/{organization.pk}/members/"
        resp = admin_client.post(url, {"username": "target", "role": "viewer"})
        assert resp.status_code == status.HTTP_201_CREATED
        membership = OrganizationMembership.objects.get(
            user=target_user, organization=organization
        )
        assert membership.role == "viewer"

    def test_invalid_role_rejected(self, admin_client, organization, target_user):
        url = f"/api/v1/auth/organizations/{organization.pk}/members/"
        resp = admin_client.post(url, {"username": "target", "role": "superadmin"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "role" in resp.data
        assert not OrganizationMembership.objects.filter(
            user=target_user, organization=organization
        ).exists()

    def test_default_role_is_member(self, admin_client, organization, target_user):
        url = f"/api/v1/auth/organizations/{organization.pk}/members/"
        resp = admin_client.post(url, {"username": "target"})
        assert resp.status_code == status.HTTP_201_CREATED
        membership = OrganizationMembership.objects.get(
            user=target_user, organization=organization
        )
        assert membership.role == "member"

    def test_empty_role_rejected(self, admin_client, organization, target_user):
        url = f"/api/v1/auth/organizations/{organization.pk}/members/"
        resp = admin_client.post(url, {"username": "target", "role": ""})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# ProblemViewSet.share() — permission validation via serializer
# ---------------------------------------------------------------------------


class TestProblemSharePermissionValidation:
    """The 'permission' field must be one of PERMISSION_CHOICES (view, comment, edit)."""

    @pytest.fixture()
    def problem(self, admin_user):
        return Problem.objects.create(
            user=admin_user,
            title="Test Problem",
            original_description="A test problem.",
        )

    def test_valid_permission_accepted(
        self, admin_client, problem, target_user
    ):
        url = f"/api/v1/problems/{problem.pk}/share/"
        resp = admin_client.post(
            url, {"username": "target", "permission": "edit"}
        )
        assert resp.status_code == status.HTTP_201_CREATED
        share = ProblemShare.objects.get(
            problem=problem, shared_with=target_user
        )
        assert share.permission == "edit"

    def test_invalid_permission_rejected(
        self, admin_client, problem, target_user
    ):
        url = f"/api/v1/problems/{problem.pk}/share/"
        resp = admin_client.post(
            url, {"username": "target", "permission": "admin"}
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "permission" in resp.data
        assert not ProblemShare.objects.filter(
            problem=problem, shared_with=target_user
        ).exists()

    def test_default_permission_is_view(
        self, admin_client, problem, target_user
    ):
        url = f"/api/v1/problems/{problem.pk}/share/"
        resp = admin_client.post(url, {"username": "target"})
        assert resp.status_code == status.HTTP_201_CREATED
        share = ProblemShare.objects.get(
            problem=problem, shared_with=target_user
        )
        assert share.permission == "view"

    def test_empty_permission_rejected(
        self, admin_client, problem, target_user
    ):
        url = f"/api/v1/problems/{problem.pk}/share/"
        resp = admin_client.post(
            url, {"username": "target", "permission": ""}
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_share_unknown_permission_value(
        self, admin_client, problem, target_user
    ):
        """Values like 'delete', 'owner', 'root' must be rejected."""
        url = f"/api/v1/problems/{problem.pk}/share/"
        for bad_perm in ("delete", "owner", "root", "superuser"):
            resp = admin_client.post(
                url, {"username": "target", "permission": bad_perm}
            )
            assert resp.status_code == status.HTTP_400_BAD_REQUEST, (
                f"permission='{bad_perm}' should be rejected"
            )

    def test_missing_username_rejected(self, admin_client, problem):
        url = f"/api/v1/problems/{problem.pk}/share/"
        resp = admin_client.post(url, {"permission": "view"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "username" in resp.data
