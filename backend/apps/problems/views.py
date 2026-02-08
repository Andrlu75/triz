from rest_framework import viewsets

from apps.problems.models import Problem
from apps.problems.serializers import ProblemListSerializer, ProblemSerializer


class ProblemViewSet(viewsets.ModelViewSet):
    """
    CRUD ViewSet for Problems.

    GET    /api/v1/problems/          — list user's problems
    POST   /api/v1/problems/          — create a new problem
    GET    /api/v1/problems/{id}/     — detail
    PATCH  /api/v1/problems/{id}/     — partial update
    DELETE /api/v1/problems/{id}/     — delete
    """

    def get_serializer_class(self):
        if self.action == "list":
            return ProblemListSerializer
        return ProblemSerializer

    def get_queryset(self):
        return Problem.objects.filter(user=self.request.user)
