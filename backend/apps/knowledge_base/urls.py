"""
URL configuration for the TRIZ Knowledge Base API.

Routes:
    /principles/              - List of TRIZ principles
    /principles/{id}/         - Principle details
    /principles/suggest/      - Suggest principles by contradiction type
    /effects/                 - List/search effects (with ?q= for vector search)
    /effects/{id}/            - Effect details
    /standards/               - List of TRIZ standards
    /standards/{id}/          - Standard details
    /analogs/                 - List of analog tasks
    /analogs/{id}/            - Analog task details
    /analogs/search/          - Vector search for analog tasks (?q=...&top_k=5)
    /definitions/             - List of 35 definitions
    /definitions/{id}/        - Definition details
    /rules/                   - List of 28 ARIZ rules
    /rules/{id}/              - Rule details
    /transformations/         - List of typical transformations
    /transformations/{id}/    - Transformation details
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.knowledge_base.views import (
    AnalogTaskSearchView,
    AnalogTaskViewSet,
    DefinitionViewSet,
    RuleViewSet,
    StandardViewSet,
    TechnologicalEffectViewSet,
    TRIZPrincipleViewSet,
    TypicalTransformationViewSet,
)

router = DefaultRouter()
router.register(r"principles", TRIZPrincipleViewSet, basename="principle")
router.register(r"effects", TechnologicalEffectViewSet, basename="effect")
router.register(r"standards", StandardViewSet, basename="standard")
router.register(r"analogs", AnalogTaskViewSet, basename="analog")
router.register(r"definitions", DefinitionViewSet, basename="definition")
router.register(r"rules", RuleViewSet, basename="rule")
router.register(r"transformations", TypicalTransformationViewSet, basename="transformation")

urlpatterns = [
    path("analogs/search/", AnalogTaskSearchView.as_view(), name="analog-search"),
    path("", include(router.urls)),
]
