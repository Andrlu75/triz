from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.problems.models import ProblemShare
from apps.users.models import Organization, OrganizationMembership
from apps.users.serializers import (
    AddMemberSerializer,
    OrganizationMembershipSerializer,
    OrganizationSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """POST /api/v1/auth/register/ — create a new user account."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class MeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/auth/me/ — current user profile."""

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class OrganizationViewSet(viewsets.ModelViewSet):
    """CRUD for organizations. Only business-plan users can create."""

    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Organization.objects.filter(
            memberships__user=self.request.user
        ).distinct()

    def perform_create(self, serializer):
        org = serializer.save()
        OrganizationMembership.objects.create(
            user=self.request.user, organization=org, role="admin"
        )
        self.request.user.organization = org
        self.request.user.save(update_fields=["organization"])

    def _is_org_admin(self, user, org):
        """Return True if user has the 'admin' role in the given organization."""
        return OrganizationMembership.objects.filter(
            user=user, organization=org, role="admin"
        ).exists()

    @action(detail=True, methods=["get", "post"], url_path="members")
    def members(self, request, pk=None):
        org = self.get_object()

        if request.method == "GET":
            memberships = OrganizationMembership.objects.filter(
                organization=org
            ).select_related("user")
            serializer = OrganizationMembershipSerializer(memberships, many=True)
            return Response(serializer.data)

        # POST — add member (admin only)
        if not self._is_org_admin(request.user, org):
            return Response(
                {"detail": "Только администратор может управлять участниками."},
                status=status.HTTP_403_FORBIDDEN,
            )

        input_serializer = AddMemberSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        username = input_serializer.validated_data["username"]
        role = input_serializer.validated_data["role"]
        user = get_object_or_404(User, username=username)

        membership, created = OrganizationMembership.objects.get_or_create(
            user=user, organization=org, defaults={"role": role}
        )
        if not created:
            return Response(
                {"detail": "Пользователь уже в организации."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.organization = org
        user.save(update_fields=["organization"])

        return Response(
            OrganizationMembershipSerializer(membership).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["delete"],
        url_path="members/(?P<user_id>[0-9]+)",
    )
    def remove_member(self, request, pk=None, user_id=None):
        org = self.get_object()

        if not self._is_org_admin(request.user, org):
            return Response(
                {"detail": "Только администратор может управлять участниками."},
                status=status.HTTP_403_FORBIDDEN,
            )

        membership = get_object_or_404(
            OrganizationMembership, organization=org, user_id=user_id
        )
        target_user = membership.user
        membership.delete()

        if target_user.organization_id == org.id:
            target_user.organization = None
            target_user.save(update_fields=["organization"])

        return Response(status=status.HTTP_204_NO_CONTENT)
