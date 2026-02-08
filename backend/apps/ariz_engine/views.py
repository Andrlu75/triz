"""
REST API views for ARIZ sessions.

Endpoints:
    POST   /sessions/start/                — start a new ARIZ session
    GET    /sessions/                       — list user's sessions
    GET    /sessions/{id}/                  — session detail
    GET    /sessions/{id}/progress/         — progress info
    GET    /sessions/{id}/current-step/     — current step + LLM result
    POST   /sessions/{id}/submit/           — submit user input → Celery task_id
    GET    /sessions/{id}/task/{task_id}/   — Celery task status
    POST   /sessions/{id}/advance/          — advance to next step
    POST   /sessions/{id}/back/             — go back one step
    GET    /sessions/{id}/summary/          — full session summary
"""
import logging

from celery.result import AsyncResult
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.ariz_engine.engine import ARIZEngine
from apps.ariz_engine.models import ARIZSession, StepResult
from apps.ariz_engine.serializers import (
    SessionListSerializer,
    SessionSerializer,
    StartSessionSerializer,
    StepResultSerializer,
    SubmitStepSerializer,
)
from apps.problems.models import Problem
from apps.users.permissions import CanUseMode

logger = logging.getLogger(__name__)


class SessionViewSet(GenericViewSet):
    """ViewSet for ARIZ session operations."""

    permission_classes = [permissions.IsAuthenticated, CanUseMode]

    def get_queryset(self):
        return ARIZSession.objects.filter(
            problem__user=self.request.user,
        ).select_related("problem")

    def get_serializer_class(self):
        if self.action == "list":
            return SessionListSerializer
        return SessionSerializer

    # ------------------------------------------------------------------
    # GET /sessions/
    # ------------------------------------------------------------------
    def list(self, request):
        queryset = self.get_queryset()
        serializer = SessionListSerializer(queryset, many=True)
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # GET /sessions/{id}/
    # ------------------------------------------------------------------
    def retrieve(self, request, pk=None):
        session = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = SessionSerializer(session)
        return Response(serializer.data)

    # ------------------------------------------------------------------
    # POST /sessions/start/
    # ------------------------------------------------------------------
    @action(detail=False, methods=["post"], url_path="start")
    def start(self, request):
        ser = StartSessionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        problem = get_object_or_404(
            Problem, pk=ser.validated_data["problem_id"], user=request.user
        )

        session = ARIZSession.objects.create(
            problem=problem,
            mode=ser.validated_data["mode"],
        )

        engine = ARIZEngine(session)
        engine.start_session()

        problem.status = "in_progress"
        problem.save(update_fields=["status"])

        return Response(
            SessionSerializer(session).data,
            status=status.HTTP_201_CREATED,
        )

    # ------------------------------------------------------------------
    # GET /sessions/{id}/progress/
    # ------------------------------------------------------------------
    @action(detail=True, methods=["get"], url_path="progress")
    def progress(self, request, pk=None):
        session = get_object_or_404(self.get_queryset(), pk=pk)
        engine = ARIZEngine(session)
        return Response(engine.get_progress())

    # ------------------------------------------------------------------
    # GET /sessions/{id}/current-step/
    # ------------------------------------------------------------------
    @action(detail=True, methods=["get"], url_path="current-step")
    def current_step(self, request, pk=None):
        session = get_object_or_404(self.get_queryset(), pk=pk)
        step_result = StepResult.objects.filter(
            session=session,
            step_code=session.current_step,
        ).first()

        if step_result is None:
            return Response(
                {"detail": "No step result found for current step."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(StepResultSerializer(step_result).data)

    # ------------------------------------------------------------------
    # POST /sessions/{id}/submit/
    # ------------------------------------------------------------------
    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        session = get_object_or_404(self.get_queryset(), pk=pk)

        ser = SubmitStepSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        engine = ARIZEngine(session)
        task_id = engine.submit_step(ser.validated_data["user_input"])

        return Response({"task_id": task_id}, status=status.HTTP_202_ACCEPTED)

    # ------------------------------------------------------------------
    # GET /sessions/{id}/task/{task_id}/
    # ------------------------------------------------------------------
    @action(
        detail=True,
        methods=["get"],
        url_path="task/(?P<task_id>[a-f0-9-]+)",
    )
    def task_status(self, request, pk=None, task_id=None):
        get_object_or_404(self.get_queryset(), pk=pk)

        result = AsyncResult(task_id)
        data = {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
        }
        if result.ready() and result.successful():
            data["result"] = result.result

        return Response(data)

    # ------------------------------------------------------------------
    # POST /sessions/{id}/advance/
    # ------------------------------------------------------------------
    @action(detail=True, methods=["post"], url_path="advance")
    def advance(self, request, pk=None):
        session = get_object_or_404(self.get_queryset(), pk=pk)
        engine = ARIZEngine(session)

        try:
            next_step = engine.advance_to_next()
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if next_step is None:
            return Response({"detail": "Session completed.", "completed": True})

        return Response(StepResultSerializer(next_step).data)

    # ------------------------------------------------------------------
    # POST /sessions/{id}/back/
    # ------------------------------------------------------------------
    @action(detail=True, methods=["post"], url_path="back")
    def back(self, request, pk=None):
        session = get_object_or_404(self.get_queryset(), pk=pk)
        engine = ARIZEngine(session)
        prev_step = engine.go_back()

        if prev_step is None:
            return Response(
                {"detail": "Already at the first step."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(StepResultSerializer(prev_step).data)

    # ------------------------------------------------------------------
    # GET /sessions/{id}/summary/
    # ------------------------------------------------------------------
    @action(detail=True, methods=["get"], url_path="summary")
    def summary(self, request, pk=None):
        session = get_object_or_404(self.get_queryset(), pk=pk)
        engine = ARIZEngine(session)
        return Response(engine.get_session_summary())
