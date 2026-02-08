from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.problems.models import Problem, ProblemShare
from apps.problems.serializers import (
    ProblemListSerializer,
    ProblemSerializer,
    ProblemShareSerializer,
    ShareProblemInputSerializer,
)
from apps.users.permissions import CanCreateProblem

User = get_user_model()


class ProblemViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Problems.

    GET    /api/v1/problems/              — list user's problems (owned + shared)
    POST   /api/v1/problems/              — create a new problem
    GET    /api/v1/problems/{id}/         — detail
    PATCH  /api/v1/problems/{id}/         — partial update
    DELETE /api/v1/problems/{id}/         — delete
    POST   /api/v1/problems/{id}/share/   — share problem with another user
    GET    /api/v1/problems/{id}/shares/  — list shares for a problem
    """

    permission_classes = [permissions.IsAuthenticated, CanCreateProblem]

    def get_serializer_class(self):
        if self.action == "list":
            return ProblemListSerializer
        return ProblemSerializer

    def get_queryset(self):
        user = self.request.user
        # Include owned problems + problems shared with this user
        return Problem.objects.filter(
            Q(user=user) | Q(shares__shared_with=user)
        ).distinct()

    @action(detail=True, methods=["post"], url_path="share")
    def share(self, request, pk=None):
        """Share a problem with another user."""
        problem = get_object_or_404(Problem, pk=pk, user=request.user)

        input_serializer = ShareProblemInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        username = input_serializer.validated_data["username"]
        permission = input_serializer.validated_data["permission"]

        target_user = get_object_or_404(User, username=username)

        if target_user == request.user:
            return Response(
                {"detail": "Нельзя поделиться задачей с самим собой."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        share, created = ProblemShare.objects.get_or_create(
            problem=problem,
            shared_with=target_user,
            defaults={"permission": permission},
        )
        if not created:
            share.permission = permission
            share.save(update_fields=["permission"])

        return Response(
            ProblemShareSerializer(share).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="shares")
    def shares(self, request, pk=None):
        """List all shares for a problem."""
        problem = get_object_or_404(Problem, pk=pk, user=request.user)
        shares = ProblemShare.objects.filter(problem=problem).select_related(
            "shared_with"
        )
        return Response(ProblemShareSerializer(shares, many=True).data)
