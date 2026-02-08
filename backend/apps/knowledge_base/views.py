"""
API views for the TRIZ Knowledge Base.

Provides read-only access to TRIZ principles, effects, standards,
analog tasks (with vector search), definitions, and rules.
"""
import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.knowledge_base.models import (
    AnalogTask,
    Definition,
    Rule,
    Standard,
    TechnologicalEffect,
    TRIZPrinciple,
    TypicalTransformation,
)
from apps.knowledge_base.search import TRIZKnowledgeSearch
from apps.knowledge_base.serializers import (
    AnalogSearchQuerySerializer,
    AnalogTaskSerializer,
    DefinitionSerializer,
    EffectSearchQuerySerializer,
    PrincipleSuggestQuerySerializer,
    RuleSerializer,
    StandardSerializer,
    TechnologicalEffectSerializer,
    TRIZPrincipleDetailSerializer,
    TRIZPrincipleListSerializer,
    TypicalTransformationSerializer,
)

logger = logging.getLogger(__name__)


class TRIZPrincipleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for TRIZ inventive principles.

    list: GET /api/v1/knowledge/principles/
    retrieve: GET /api/v1/knowledge/principles/{id}/
    suggest: GET /api/v1/knowledge/principles/suggest/?contradiction_type=...
    """

    queryset = TRIZPrinciple.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TRIZPrincipleDetailSerializer
        return TRIZPrincipleListSerializer

    @action(detail=False, methods=["get"])
    def suggest(self, request):
        """
        Suggest principles based on contradiction type.

        Query params:
            contradiction_type: "surface" | "deepened" | "sharpened"
            formulation: optional contradiction text
        """
        query_serializer = PrincipleSuggestQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        search = TRIZKnowledgeSearch()
        principles = search.suggest_principles(
            contradiction_type=query_serializer.validated_data["contradiction_type"],
            formulation=query_serializer.validated_data.get("formulation", ""),
        )

        serializer = TRIZPrincipleDetailSerializer(principles, many=True)
        return Response(serializer.data)


class TechnologicalEffectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for technological effects with vector search.

    list: GET /api/v1/knowledge/effects/
    search (via list with ?q=): GET /api/v1/knowledge/effects/?q=...
    retrieve: GET /api/v1/knowledge/effects/{id}/
    """

    queryset = TechnologicalEffect.objects.all()
    serializer_class = TechnologicalEffectSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        """
        List effects, optionally filtered by vector search.

        If `q` query parameter is provided, performs semantic search
        using pgvector cosine distance.
        """
        query = request.query_params.get("q", "").strip()

        if query:
            query_serializer = EffectSearchQuerySerializer(data=request.query_params)
            query_serializer.is_valid(raise_exception=True)

            search = TRIZKnowledgeSearch()
            effects = search.find_effects(
                function_description=query_serializer.validated_data["q"],
                top_k=query_serializer.validated_data.get("top_k", 5),
            )
            serializer = self.get_serializer(effects, many=True)
            return Response(serializer.data)

        return super().list(request, *args, **kwargs)


class StandardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for TRIZ standards.

    list: GET /api/v1/knowledge/standards/
    retrieve: GET /api/v1/knowledge/standards/{id}/
    """

    queryset = Standard.objects.all()
    serializer_class = StandardSerializer
    permission_classes = [AllowAny]


class AnalogTaskSearchView(APIView):
    """
    Vector search for analog tasks by OP formulation.

    GET /api/v1/knowledge/analogs/search/?q=...&top_k=5
    """

    permission_classes = [AllowAny]

    def get(self, request):
        query_serializer = AnalogSearchQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        search = TRIZKnowledgeSearch()
        analogs = search.search_analog_tasks(
            op_formulation=query_serializer.validated_data["q"],
            top_k=query_serializer.validated_data.get("top_k", 5),
        )

        serializer = AnalogTaskSerializer(analogs, many=True)
        return Response(serializer.data)


class AnalogTaskViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for analog tasks (CRUD-like read access).

    list: GET /api/v1/knowledge/analogs/
    retrieve: GET /api/v1/knowledge/analogs/{id}/
    """

    queryset = AnalogTask.objects.all()
    serializer_class = AnalogTaskSerializer
    permission_classes = [AllowAny]


class DefinitionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for TRIZ definitions (35 terms from Appendix 4).

    list: GET /api/v1/knowledge/definitions/
    retrieve: GET /api/v1/knowledge/definitions/{id}/
    """

    queryset = Definition.objects.all()
    serializer_class = DefinitionSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Return all 35 definitions without pagination


class RuleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for ARIZ rules (28 rules).

    list: GET /api/v1/knowledge/rules/
    retrieve: GET /api/v1/knowledge/rules/{id}/
    """

    queryset = Rule.objects.all()
    serializer_class = RuleSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Return all 28 rules without pagination


class TypicalTransformationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for typical transformations.

    list: GET /api/v1/knowledge/transformations/
    retrieve: GET /api/v1/knowledge/transformations/{id}/
    """

    queryset = TypicalTransformation.objects.all()
    serializer_class = TypicalTransformationSerializer
    permission_classes = [AllowAny]
