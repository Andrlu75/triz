"""
Batch embedding generation with Redis caching.

Provides efficient embedding creation for TRIZ knowledge base items
using OpenAI text-embedding-3-small model (1536 dimensions).
"""
import hashlib
import json
import logging
from typing import Sequence

from django.core.cache import cache

from apps.llm_service.client import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL, OpenAIClient

logger = logging.getLogger(__name__)

# Maximum texts per single OpenAI Embeddings API request
BATCH_SIZE = 2048

# Redis cache key prefix and TTL (7 days)
CACHE_KEY_PREFIX = "emb:v1:"
CACHE_TTL = 60 * 60 * 24 * 7


def _cache_key(text: str) -> str:
    """
    Generate a deterministic Redis cache key for an embedding.

    Uses SHA-256 hash of the text to avoid key-length issues.
    """
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"{CACHE_KEY_PREFIX}{text_hash}"


def get_cached_embedding(text: str) -> list[float] | None:
    """
    Retrieve a cached embedding vector from Redis.

    Args:
        text: The original text whose embedding was cached.

    Returns:
        The embedding vector as a list of floats, or None if not cached.
    """
    key = _cache_key(text)
    raw = cache.get(key)
    if raw is not None:
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Corrupt cached embedding for key %s, ignoring", key)
            cache.delete(key)
    return None


def cache_embedding(text: str, vector: list[float]) -> None:
    """
    Store an embedding vector in Redis cache.

    Args:
        text: The original text.
        vector: The embedding vector to cache.
    """
    key = _cache_key(text)
    cache.set(key, json.dumps(vector), timeout=CACHE_TTL)


def create_single_embedding(
    text: str,
    client: OpenAIClient | None = None,
    use_cache: bool = True,
) -> list[float]:
    """
    Generate an embedding for a single text, with optional Redis caching.

    Args:
        text: Text to embed.
        client: Optional pre-initialized OpenAIClient instance.
        use_cache: Whether to check/store in Redis cache.

    Returns:
        Embedding vector as a list of 1536 floats.
    """
    if use_cache:
        cached = get_cached_embedding(text)
        if cached is not None:
            logger.debug("Cache hit for embedding (text length=%d)", len(text))
            return cached

    if client is None:
        client = OpenAIClient()

    response = client.create_embedding(text)
    vector = response.vector

    if use_cache:
        cache_embedding(text, vector)

    return vector


def create_batch_embeddings(
    texts: Sequence[str],
    client: OpenAIClient | None = None,
    use_cache: bool = True,
) -> list[list[float]]:
    """
    Generate embeddings for multiple texts in batches of up to 2048.

    Checks Redis cache first for each text, only sends uncached texts
    to the OpenAI API. Results are stored back in the cache.

    Args:
        texts: Sequence of texts to embed.
        client: Optional pre-initialized OpenAIClient instance.
        use_cache: Whether to use Redis caching.

    Returns:
        List of embedding vectors in the same order as the input texts.
    """
    if not texts:
        return []

    if client is None:
        client = OpenAIClient()

    # Initialize result slots
    results: list[list[float] | None] = [None] * len(texts)

    # Check cache for all texts
    uncached_indices: list[int] = []
    uncached_texts: list[str] = []

    for i, text in enumerate(texts):
        if use_cache:
            cached = get_cached_embedding(text)
            if cached is not None:
                results[i] = cached
                continue
        uncached_indices.append(i)
        uncached_texts.append(text)

    if uncached_texts:
        logger.info(
            "Generating embeddings: %d cached, %d to generate",
            len(texts) - len(uncached_texts),
            len(uncached_texts),
        )

        # Process in batches of BATCH_SIZE
        for batch_start in range(0, len(uncached_texts), BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, len(uncached_texts))
            batch_texts = uncached_texts[batch_start:batch_end]

            batch_vectors = _call_embeddings_api(client, batch_texts)

            for j, vector in enumerate(batch_vectors):
                original_idx = uncached_indices[batch_start + j]
                results[original_idx] = vector

                if use_cache:
                    cache_embedding(uncached_texts[batch_start + j], vector)

    # All slots should be filled now
    return results  # type: ignore[return-value]


def _call_embeddings_api(
    client: OpenAIClient,
    texts: list[str],
) -> list[list[float]]:
    """
    Call the OpenAI Embeddings API for a batch of texts.

    Uses the raw OpenAI client to send multiple texts in a single request
    for efficiency.

    Args:
        client: Initialized OpenAIClient instance.
        texts: List of texts (max 2048 per call).

    Returns:
        List of embedding vectors.
    """
    raw = client._client.embeddings.create(
        input=texts,
        model=EMBEDDING_MODEL,
        dimensions=EMBEDDING_DIMENSIONS,
    )

    # Sort by index to maintain order
    sorted_data = sorted(raw.data, key=lambda x: x.index)
    vectors = [item.embedding for item in sorted_data]

    total_tokens = raw.usage.prompt_tokens if raw.usage else 0
    cost = OpenAIClient.calculate_cost(total_tokens, 0, EMBEDDING_MODEL)

    logger.info(
        "Batch embedding: %d texts, %d tokens, cost=$%.6f",
        len(texts),
        total_tokens,
        cost,
    )

    return vectors
