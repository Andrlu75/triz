"""
Tests for TRIZ Knowledge Base vector search functionality.

Covers:
    - TRIZKnowledgeSearch.search_analog_tasks()
    - TRIZKnowledgeSearch.suggest_principles()
    - TRIZKnowledgeSearch.find_effects()
    - Embedding generation and caching
"""
import json
from unittest.mock import MagicMock, patch

import pytest
from django.test import TestCase, override_settings

from apps.knowledge_base.models import (
    AnalogTask,
    TechnologicalEffect,
    TRIZPrinciple,
    TypicalTransformation,
)
from apps.knowledge_base.search import TRIZKnowledgeSearch
from apps.llm_service.embeddings import (
    CACHE_KEY_PREFIX,
    _cache_key,
    cache_embedding,
    create_batch_embeddings,
    create_single_embedding,
    get_cached_embedding,
)


def _fake_vector(seed: float = 0.1) -> list[float]:
    """Generate a deterministic fake embedding vector (1536 dims)."""
    import math
    return [math.sin(seed * (i + 1)) * 0.5 for i in range(1536)]


def _mock_embedding_response(vector: list[float]):
    """Create a mock EmbeddingResponse."""
    mock = MagicMock()
    mock.vector = vector
    mock.model = "text-embedding-3-small"
    mock.input_tokens = 10
    mock.cost_usd = 0.000001
    return mock


class TestCacheKey(TestCase):
    """Test cache key generation."""

    def test_cache_key_deterministic(self):
        key1 = _cache_key("test text")
        key2 = _cache_key("test text")
        assert key1 == key2

    def test_cache_key_prefix(self):
        key = _cache_key("anything")
        assert key.startswith(CACHE_KEY_PREFIX)

    def test_different_texts_different_keys(self):
        key1 = _cache_key("text one")
        key2 = _cache_key("text two")
        assert key1 != key2


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class TestEmbeddingCache(TestCase):
    """Test Redis caching of embeddings."""

    def test_cache_round_trip(self):
        vector = _fake_vector(0.5)
        cache_embedding("test text", vector)

        cached = get_cached_embedding("test text")
        assert cached is not None
        assert len(cached) == 1536
        assert cached[0] == pytest.approx(vector[0], abs=1e-6)

    def test_cache_miss(self):
        cached = get_cached_embedding("nonexistent text")
        assert cached is None

    @patch("apps.llm_service.embeddings.OpenAIClient")
    def test_create_single_embedding_with_cache(self, MockClient):
        vector = _fake_vector(0.3)
        mock_client = MockClient.return_value
        mock_client.create_embedding.return_value = _mock_embedding_response(vector)

        # First call — should hit API
        result1 = create_single_embedding("hello world", client=mock_client)
        assert len(result1) == 1536
        mock_client.create_embedding.assert_called_once()

        # Second call — should hit cache
        result2 = create_single_embedding("hello world", client=mock_client)
        assert result2 == result1
        # Still only one API call
        mock_client.create_embedding.assert_called_once()

    @patch("apps.llm_service.embeddings.OpenAIClient")
    def test_create_single_embedding_no_cache(self, MockClient):
        vector = _fake_vector(0.4)
        mock_client = MockClient.return_value
        mock_client.create_embedding.return_value = _mock_embedding_response(vector)

        result = create_single_embedding("test", client=mock_client, use_cache=False)
        assert len(result) == 1536
        mock_client.create_embedding.assert_called_once()


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class TestBatchEmbeddings(TestCase):
    """Test batch embedding generation."""

    @patch("apps.llm_service.embeddings._call_embeddings_api")
    @patch("apps.llm_service.embeddings.OpenAIClient")
    def test_batch_embeddings_all_uncached(self, MockClient, mock_api):
        vectors = [_fake_vector(i * 0.1) for i in range(3)]
        mock_api.return_value = vectors
        mock_client = MockClient.return_value

        texts = ["text one", "text two", "text three"]
        results = create_batch_embeddings(texts, client=mock_client)

        assert len(results) == 3
        mock_api.assert_called_once()

    @patch("apps.llm_service.embeddings._call_embeddings_api")
    @patch("apps.llm_service.embeddings.OpenAIClient")
    def test_batch_embeddings_partial_cache(self, MockClient, mock_api):
        # Pre-cache one embedding
        cached_vector = _fake_vector(0.9)
        cache_embedding("text two", cached_vector)

        uncached_vectors = [_fake_vector(0.1), _fake_vector(0.3)]
        mock_api.return_value = uncached_vectors
        mock_client = MockClient.return_value

        texts = ["text one", "text two", "text three"]
        results = create_batch_embeddings(texts, client=mock_client)

        assert len(results) == 3
        # Only 2 texts should be sent to API
        call_args = mock_api.call_args[0]
        assert len(call_args[1]) == 2

    def test_batch_embeddings_empty_list(self):
        results = create_batch_embeddings([])
        assert results == []


@pytest.mark.django_db
class TestSearchAnalogTasks(TestCase):
    """Test TRIZKnowledgeSearch.search_analog_tasks()."""

    def setUp(self):
        self.search = TRIZKnowledgeSearch()

        # Create analog tasks with embeddings
        self.task1 = AnalogTask.objects.create(
            title="Task about heat transfer",
            problem_description="How to improve heat transfer in a pipe",
            op_formulation="The pipe must be thin to fit, but thick to conduct heat",
            solution_principle="Use internal fins",
            domain="thermal",
            embedding=_fake_vector(0.1),
        )
        self.task2 = AnalogTask.objects.create(
            title="Task about weight reduction",
            problem_description="Reduce aircraft weight",
            op_formulation="The wing must be heavy to be strong, but light to fly",
            solution_principle="Use composite materials",
            domain="aerospace",
            embedding=_fake_vector(0.5),
        )
        self.task3 = AnalogTask.objects.create(
            title="Task without embedding",
            problem_description="Some problem",
            op_formulation="Some contradiction",
            solution_principle="Some solution",
            domain="general",
            embedding=None,
        )

    @patch("apps.knowledge_base.search.create_single_embedding")
    def test_search_returns_results(self, mock_embed):
        mock_embed.return_value = _fake_vector(0.1)

        results = self.search.search_analog_tasks("heat transfer contradiction")
        assert len(results) >= 1
        # Tasks without embeddings should be excluded
        for r in results:
            assert r.embedding is not None

    @patch("apps.knowledge_base.search.create_single_embedding")
    def test_search_respects_top_k(self, mock_embed):
        mock_embed.return_value = _fake_vector(0.1)

        results = self.search.search_analog_tasks("test query", top_k=1)
        assert len(results) <= 1

    def test_search_empty_query(self):
        results = self.search.search_analog_tasks("")
        assert results == []

    def test_search_whitespace_query(self):
        results = self.search.search_analog_tasks("   ")
        assert results == []

    @patch("apps.knowledge_base.search.create_single_embedding")
    def test_search_annotates_distance(self, mock_embed):
        mock_embed.return_value = _fake_vector(0.1)

        results = self.search.search_analog_tasks("heat query")
        assert len(results) > 0
        # Results should have distance annotation
        assert hasattr(results[0], "distance")


@pytest.mark.django_db
class TestSuggestPrinciples(TestCase):
    """Test TRIZKnowledgeSearch.suggest_principles()."""

    def setUp(self):
        self.search = TRIZKnowledgeSearch()

        # Create some principles
        for i in range(1, 8):
            TRIZPrinciple.objects.create(
                number=i,
                name=f"Principle {i}",
                description=f"Description of principle {i}",
                is_additional=False,
            )

        # Create a transformation
        TypicalTransformation.objects.create(
            contradiction_type="sharpened",
            transformation="Principle 1",
            description="Use segmentation to resolve sharpened contradictions",
        )

    def test_suggest_with_matching_transformation(self):
        results = self.search.suggest_principles(
            contradiction_type="sharpened",
        )
        assert len(results) >= 1

    def test_suggest_fallback_to_classical(self):
        results = self.search.suggest_principles(
            contradiction_type="nonexistent",
        )
        # Should return up to 5 classical principles as fallback
        assert len(results) <= 5
        assert len(results) > 0
        for p in results:
            assert not p.is_additional

    def test_suggest_with_formulation(self):
        results = self.search.suggest_principles(
            contradiction_type="deepened",
            formulation="segmentation needed for the structure",
        )
        assert len(results) > 0


@pytest.mark.django_db
class TestFindEffects(TestCase):
    """Test TRIZKnowledgeSearch.find_effects()."""

    def setUp(self):
        self.search = TRIZKnowledgeSearch()

        self.effect1 = TechnologicalEffect.objects.create(
            type="physical",
            name="Thermal expansion",
            description="Materials expand when heated",
            function_keywords=["heating", "expansion", "temperature"],
            embedding=_fake_vector(0.2),
        )
        self.effect2 = TechnologicalEffect.objects.create(
            type="chemical",
            name="Oxidation",
            description="Chemical reaction with oxygen",
            function_keywords=["oxidation", "corrosion", "reaction"],
            embedding=_fake_vector(0.7),
        )
        self.effect_no_embedding = TechnologicalEffect.objects.create(
            type="biological",
            name="Osmosis",
            description="Movement through membrane",
            function_keywords=["membrane", "diffusion"],
            embedding=None,
        )

    @patch("apps.knowledge_base.search.create_single_embedding")
    def test_find_effects_returns_results(self, mock_embed):
        mock_embed.return_value = _fake_vector(0.2)

        results = self.search.find_effects("heat expansion of materials")
        assert len(results) >= 1
        for r in results:
            assert r.embedding is not None

    @patch("apps.knowledge_base.search.create_single_embedding")
    def test_find_effects_respects_top_k(self, mock_embed):
        mock_embed.return_value = _fake_vector(0.2)

        results = self.search.find_effects("test", top_k=1)
        assert len(results) <= 1

    def test_find_effects_empty_query(self):
        results = self.search.find_effects("")
        assert results == []

    def test_search_effects_by_keywords(self):
        results = self.search.search_effects_by_keywords(["heating"])
        assert len(results) >= 1
        assert results[0].name == "Thermal expansion"

    def test_search_effects_by_keywords_empty(self):
        results = self.search.search_effects_by_keywords([])
        assert results == []
