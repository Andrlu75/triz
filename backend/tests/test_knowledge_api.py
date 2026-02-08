"""
Tests for TRIZ Knowledge Base REST API endpoints.

Covers:
    - GET /api/v1/knowledge/principles/ (list + retrieve + suggest)
    - GET /api/v1/knowledge/effects/ (list + search)
    - GET /api/v1/knowledge/standards/ (list + retrieve)
    - GET /api/v1/knowledge/analogs/search/ (vector search)
    - GET /api/v1/knowledge/definitions/ (list)
    - GET /api/v1/knowledge/rules/ (list)
"""
import math
from unittest.mock import patch

import pytest
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.knowledge_base.models import (
    AnalogTask,
    Definition,
    Rule,
    Standard,
    TechnologicalEffect,
    TRIZPrinciple,
    TypicalTransformation,
)


def _fake_vector(seed: float = 0.1) -> list[float]:
    """Generate a deterministic fake embedding vector (1536 dims)."""
    return [math.sin(seed * (i + 1)) * 0.5 for i in range(1536)]


@pytest.mark.django_db
class TestPrincipleAPI(TestCase):
    """Test /api/v1/knowledge/principles/ endpoints."""

    def setUp(self):
        self.client = APIClient()

        self.principle1 = TRIZPrinciple.objects.create(
            number=1,
            name="Segmentation",
            description="Divide an object into independent parts.",
            examples=["Modular furniture", "Sectioned containers"],
            is_additional=False,
        )
        self.principle2 = TRIZPrinciple.objects.create(
            number=2,
            name="Taking out",
            description="Separate an interfering part.",
            examples=["Remote control"],
            is_additional=False,
        )
        self.principle41 = TRIZPrinciple.objects.create(
            number=41,
            name="Additional principle",
            description="An additional principle by Petrov.",
            is_additional=True,
        )

    def test_list_principles(self):
        response = self.client.get("/api/v1/knowledge/principles/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # May be paginated
        results = data.get("results", data)
        assert len(results) == 3

    def test_retrieve_principle(self):
        response = self.client.get(
            f"/api/v1/knowledge/principles/{self.principle1.pk}/"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["number"] == 1
        assert data["name"] == "Segmentation"
        assert "description" in data
        assert "examples" in data

    def test_retrieve_nonexistent_principle(self):
        response = self.client.get("/api/v1/knowledge/principles/9999/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_suggest_principles(self):
        TypicalTransformation.objects.create(
            contradiction_type="sharpened",
            transformation="Segmentation",
            description="Use segmentation for resolution",
        )

        response = self.client.get(
            "/api/v1/knowledge/principles/suggest/",
            {"contradiction_type": "sharpened"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_suggest_principles_missing_type(self):
        response = self.client.get("/api/v1/knowledge/principles/suggest/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_suggest_principles_invalid_type(self):
        response = self.client.get(
            "/api/v1/knowledge/principles/suggest/",
            {"contradiction_type": "invalid"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestEffectAPI(TestCase):
    """Test /api/v1/knowledge/effects/ endpoints."""

    def setUp(self):
        self.client = APIClient()

        self.effect1 = TechnologicalEffect.objects.create(
            type="physical",
            name="Thermal expansion",
            description="Materials expand when heated.",
            function_keywords=["heating", "expansion"],
            embedding=_fake_vector(0.2),
        )
        self.effect2 = TechnologicalEffect.objects.create(
            type="chemical",
            name="Oxidation",
            description="Reaction with oxygen.",
            function_keywords=["oxidation"],
            embedding=_fake_vector(0.7),
        )

    def test_list_effects(self):
        response = self.client.get("/api/v1/knowledge/effects/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        results = data.get("results", data)
        assert len(results) == 2

    def test_retrieve_effect(self):
        response = self.client.get(
            f"/api/v1/knowledge/effects/{self.effect1.pk}/"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Thermal expansion"
        assert data["type"] == "physical"
        assert data["type_display"] == "Physical"

    @patch("apps.knowledge_base.search.create_single_embedding")
    def test_search_effects(self, mock_embed):
        mock_embed.return_value = _fake_vector(0.2)

        response = self.client.get(
            "/api/v1/knowledge/effects/",
            {"q": "heat transfer"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # When searching, results are returned as a plain list (not paginated)
        assert isinstance(data, list)
        assert len(data) >= 1


@pytest.mark.django_db
class TestStandardAPI(TestCase):
    """Test /api/v1/knowledge/standards/ endpoints."""

    def setUp(self):
        self.client = APIClient()

        self.standard = Standard.objects.create(
            class_number=1,
            number="1.1.1",
            name="Building a vepol",
            description="If an object is not controllable, build a vepol.",
            applicability="When the object needs to be controlled.",
        )

    def test_list_standards(self):
        response = self.client.get("/api/v1/knowledge/standards/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        results = data.get("results", data)
        assert len(results) == 1

    def test_retrieve_standard(self):
        response = self.client.get(
            f"/api/v1/knowledge/standards/{self.standard.pk}/"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["number"] == "1.1.1"
        assert data["class_number"] == 1


@pytest.mark.django_db
class TestAnalogSearchAPI(TestCase):
    """Test /api/v1/knowledge/analogs/search/ endpoint."""

    def setUp(self):
        self.client = APIClient()

        self.analog1 = AnalogTask.objects.create(
            title="Heat pipe optimization",
            problem_description="Improve heat transfer in narrow pipes",
            op_formulation="Pipe must be thin to fit but thick to transfer heat",
            solution_principle="Use internal micro-fins",
            domain="thermal",
            embedding=_fake_vector(0.1),
        )
        self.analog2 = AnalogTask.objects.create(
            title="Lightweight wing",
            problem_description="Reduce weight while maintaining strength",
            op_formulation="Wing must be heavy to be strong but light to fly",
            solution_principle="Carbon fiber composites",
            domain="aerospace",
            embedding=_fake_vector(0.5),
        )

    @patch("apps.knowledge_base.search.create_single_embedding")
    def test_search_analogs(self, mock_embed):
        mock_embed.return_value = _fake_vector(0.1)

        response = self.client.get(
            "/api/v1/knowledge/analogs/search/",
            {"q": "pipe heat transfer contradiction"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "title" in data[0]
        assert "op_formulation" in data[0]

    @patch("apps.knowledge_base.search.create_single_embedding")
    def test_search_analogs_with_top_k(self, mock_embed):
        mock_embed.return_value = _fake_vector(0.1)

        response = self.client.get(
            "/api/v1/knowledge/analogs/search/",
            {"q": "test", "top_k": 1},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) <= 1

    def test_search_analogs_missing_query(self):
        response = self.client.get("/api/v1/knowledge/analogs/search/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("apps.knowledge_base.search.create_single_embedding")
    def test_search_analogs_has_distance(self, mock_embed):
        mock_embed.return_value = _fake_vector(0.1)

        response = self.client.get(
            "/api/v1/knowledge/analogs/search/",
            {"q": "test query"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        # Distance should be present in results
        assert "distance" in data[0]

    def test_analog_list(self):
        response = self.client.get("/api/v1/knowledge/analogs/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        results = data.get("results", data)
        assert len(results) == 2

    def test_analog_retrieve(self):
        response = self.client.get(
            f"/api/v1/knowledge/analogs/{self.analog1.pk}/"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Heat pipe optimization"


@pytest.mark.django_db
class TestDefinitionAPI(TestCase):
    """Test /api/v1/knowledge/definitions/ endpoints."""

    def setUp(self):
        self.client = APIClient()

        for i in range(1, 6):
            Definition.objects.create(
                number=i,
                term=f"Term {i}",
                definition=f"Definition of term {i}",
            )

    def test_list_definitions(self):
        response = self.client.get("/api/v1/knowledge/definitions/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # No pagination for definitions
        assert isinstance(data, list)
        assert len(data) == 5

    def test_retrieve_definition(self):
        defn = Definition.objects.first()
        response = self.client.get(
            f"/api/v1/knowledge/definitions/{defn.pk}/"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "term" in data
        assert "definition" in data


@pytest.mark.django_db
class TestRuleAPI(TestCase):
    """Test /api/v1/knowledge/rules/ endpoints."""

    def setUp(self):
        self.client = APIClient()

        for i in range(1, 4):
            Rule.objects.create(
                number=i,
                name=f"Rule {i}",
                description=f"Description of rule {i}",
                examples=[f"Example for rule {i}"],
            )

    def test_list_rules(self):
        response = self.client.get("/api/v1/knowledge/rules/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # No pagination for rules
        assert isinstance(data, list)
        assert len(data) == 3

    def test_retrieve_rule(self):
        rule = Rule.objects.first()
        response = self.client.get(
            f"/api/v1/knowledge/rules/{rule.pk}/"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "name" in data
        assert "description" in data
        assert "examples" in data


@pytest.mark.django_db
class TestTransformationAPI(TestCase):
    """Test /api/v1/knowledge/transformations/ endpoints."""

    def setUp(self):
        self.client = APIClient()

        TypicalTransformation.objects.create(
            contradiction_type="sharpened",
            transformation="Segmentation",
            description="Split into parts",
        )

    def test_list_transformations(self):
        response = self.client.get("/api/v1/knowledge/transformations/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        results = data.get("results", data)
        assert len(results) == 1

    def test_retrieve_transformation(self):
        t = TypicalTransformation.objects.first()
        response = self.client.get(
            f"/api/v1/knowledge/transformations/{t.pk}/"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["contradiction_type"] == "sharpened"
        assert data["transformation"] == "Segmentation"
