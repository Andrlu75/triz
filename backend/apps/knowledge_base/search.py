"""
TRIZ Knowledge Base vector search and knowledge retrieval.

Provides semantic search over analog tasks and technological effects
using pgvector cosine distance, plus rule-based principle suggestion.
"""
import logging
from typing import Sequence

from pgvector.django import CosineDistance

from apps.knowledge_base.models import (
    AnalogTask,
    TechnologicalEffect,
    TRIZPrinciple,
    TypicalTransformation,
)
from apps.llm_service.embeddings import create_single_embedding

logger = logging.getLogger(__name__)


class TRIZKnowledgeSearch:
    """
    Unified search interface for the TRIZ knowledge base.

    Methods:
        search_analog_tasks: Semantic search for analog tasks by OP formulation.
        suggest_principles: Suggest inventive principles based on contradiction type.
        find_effects: Semantic search for technological effects by function description.
    """

    def search_analog_tasks(
        self,
        op_formulation: str,
        top_k: int = 5,
    ) -> list[AnalogTask]:
        """
        Search for analog tasks by Sharpened Contradiction (OP) formulation.

        Uses pgvector cosine distance to find the most semantically similar
        analog tasks based on their OP formulation embeddings.

        Args:
            op_formulation: The OP formulation text to search for.
            top_k: Maximum number of results to return.

        Returns:
            List of AnalogTask instances ordered by similarity (closest first).
        """
        if not op_formulation.strip():
            return []

        query_vector = create_single_embedding(op_formulation)

        results = (
            AnalogTask.objects
            .exclude(embedding__isnull=True)
            .annotate(distance=CosineDistance("embedding", query_vector))
            .order_by("distance")[:top_k]
        )

        logger.info(
            "Analog task search: query_len=%d results=%d",
            len(op_formulation),
            len(results),
        )

        return list(results)

    def suggest_principles(
        self,
        contradiction_type: str,
        formulation: str = "",
    ) -> list[TRIZPrinciple]:
        """
        Suggest inventive principles based on contradiction type.

        Uses typical transformations to find matching contradiction types,
        then maps transformations back to principles by keyword matching.
        Falls back to returning the first 5 classical principles if no
        specific match is found.

        Args:
            contradiction_type: Type of contradiction ("surface", "deepened", "sharpened").
            formulation: Optional text of the contradiction formulation for context.

        Returns:
            List of suggested TRIZPrinciple instances.
        """
        # Find typical transformations matching this contradiction type
        transformations = TypicalTransformation.objects.filter(
            contradiction_type__icontains=contradiction_type,
        )

        if not transformations.exists() and formulation:
            # Try searching by keywords from the formulation
            keywords = formulation.split()[:5]
            for keyword in keywords:
                if len(keyword) > 3:
                    transformations = TypicalTransformation.objects.filter(
                        description__icontains=keyword,
                    )
                    if transformations.exists():
                        break

        if transformations.exists():
            # Extract principle names/numbers from transformation descriptions
            principle_ids = set()
            for t in transformations:
                # Try to find principles whose name appears in the transformation
                matched = TRIZPrinciple.objects.filter(
                    name__icontains=t.transformation,
                )
                for p in matched:
                    principle_ids.add(p.pk)

            if principle_ids:
                principles = list(
                    TRIZPrinciple.objects
                    .filter(pk__in=principle_ids)
                    .order_by("number")
                )
                logger.info(
                    "Suggest principles: type=%s found=%d via transformations",
                    contradiction_type,
                    len(principles),
                )
                return principles

        # Fallback: return first 5 classical (non-additional) principles
        fallback = list(
            TRIZPrinciple.objects
            .filter(is_additional=False)
            .order_by("number")[:5]
        )
        logger.info(
            "Suggest principles: type=%s fallback=%d classical principles",
            contradiction_type,
            len(fallback),
        )
        return fallback

    def find_effects(
        self,
        function_description: str,
        top_k: int = 5,
    ) -> list[TechnologicalEffect]:
        """
        Search for technological effects by function description.

        Uses pgvector cosine distance on effect embeddings to find effects
        whose descriptions are semantically closest to the query.

        Args:
            function_description: Description of the function to search for.
            top_k: Maximum number of results to return.

        Returns:
            List of TechnologicalEffect instances ordered by similarity.
        """
        if not function_description.strip():
            return []

        query_vector = create_single_embedding(function_description)

        results = (
            TechnologicalEffect.objects
            .exclude(embedding__isnull=True)
            .annotate(distance=CosineDistance("embedding", query_vector))
            .order_by("distance")[:top_k]
        )

        logger.info(
            "Effect search: query_len=%d results=%d",
            len(function_description),
            len(results),
        )

        return list(results)

    def search_effects_by_keywords(
        self,
        keywords: Sequence[str],
    ) -> list[TechnologicalEffect]:
        """
        Search for effects by function keywords (exact match in JSON array).

        This is a fallback method when embeddings are not available.

        Args:
            keywords: List of keyword strings to search for.

        Returns:
            List of matching TechnologicalEffect instances.
        """
        from django.db.models import Q

        if not keywords:
            return []

        query = Q()
        for kw in keywords:
            query |= Q(function_keywords__contains=[kw])

        results = list(
            TechnologicalEffect.objects.filter(query).order_by("type", "name")
        )

        logger.info(
            "Keyword effect search: keywords=%s results=%d",
            keywords,
            len(results),
        )

        return results
