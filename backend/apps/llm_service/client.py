"""
OpenAI API client wrapper with retry logic and cost tracking.
"""
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from django.conf import settings
from openai import APIConnectionError, APITimeoutError, OpenAI, RateLimitError

logger = logging.getLogger(__name__)

# Pricing per 1M tokens (USD) — GPT-4o and GPT-4o-mini
MODEL_PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "text-embedding-3-small": {"input": 0.02, "output": 0.0},
}

DEFAULT_MODEL = "gpt-4o"
VALIDATION_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536

MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds
RETRY_MAX_DELAY = 30.0  # seconds
REQUEST_TIMEOUT = 120  # seconds

RETRYABLE_EXCEPTIONS = (APIConnectionError, APITimeoutError, RateLimitError)


@dataclass
class LLMResponse:
    """Structured response from the OpenAI API."""

    content: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    finish_reason: str
    latency_ms: float


@dataclass
class EmbeddingResponse:
    """Structured response from the OpenAI Embeddings API."""

    vector: list[float]
    model: str
    input_tokens: int
    cost_usd: float


@dataclass
class UsageStats:
    """Accumulated usage statistics."""

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    request_count: int = 0
    errors: list[dict[str, Any]] = field(default_factory=list)

    def record(self, response: LLMResponse) -> None:
        self.total_input_tokens += response.input_tokens
        self.total_output_tokens += response.output_tokens
        self.total_cost_usd += response.cost_usd
        self.request_count += 1


class OpenAIClient:
    """
    Wrapper around openai.OpenAI with retry logic, cost tracking, and timeouts.

    Usage::

        client = OpenAIClient()
        response = client.send_message(
            system_prompt="You are a TRIZ expert.",
            messages=[{"role": "user", "content": "Describe the problem."}],
        )
        print(response.content)
    """

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = DEFAULT_MODEL,
        timeout: int = REQUEST_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        resolved_key = api_key or getattr(settings, "OPENAI_API_KEY", "")
        if not resolved_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY in Django settings "
                "or pass api_key explicitly."
            )

        self._client = OpenAI(api_key=resolved_key, timeout=timeout)
        self.default_model = default_model
        self.timeout = timeout
        self.max_retries = max_retries
        self.usage = UsageStats()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_message(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        max_tokens: int = 4096,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Send a chat completion request to OpenAI.

        Args:
            system_prompt: System-level instruction for the model.
            messages: List of {"role": ..., "content": ...} dicts.
            max_tokens: Maximum tokens in the response.
            model: Model override (defaults to self.default_model).
            temperature: Sampling temperature (0.0 – 2.0).

        Returns:
            LLMResponse with content, token counts, cost, and latency.

        Raises:
            openai.OpenAIError on non-retryable failures.
        """
        chosen_model = model or self.default_model
        full_messages = [{"role": "system", "content": system_prompt}] + messages

        response = self._request_with_retry(
            chosen_model, full_messages, max_tokens, temperature
        )
        return response

    def send_validation(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """
        Send a validation request using the cheaper GPT-4o-mini model.
        """
        return self.send_message(
            system_prompt=system_prompt,
            messages=messages,
            max_tokens=max_tokens,
            model=VALIDATION_MODEL,
            temperature=0.3,
        )

    def create_embedding(
        self,
        text: str,
        model: str = EMBEDDING_MODEL,
        dimensions: int = EMBEDDING_DIMENSIONS,
    ) -> EmbeddingResponse:
        """
        Generate an embedding vector for the given text.

        Args:
            text: Input text to embed.
            model: Embedding model name.
            dimensions: Vector dimensions.

        Returns:
            EmbeddingResponse with the vector and usage info.
        """
        start = time.monotonic()
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            try:
                raw = self._client.embeddings.create(
                    input=text,
                    model=model,
                    dimensions=dimensions,
                )
                elapsed_ms = (time.monotonic() - start) * 1000
                usage = raw.usage
                cost = self.calculate_cost(usage.prompt_tokens, 0, model)

                logger.info(
                    "Embedding created: model=%s tokens=%d cost=$%.6f latency=%.0fms",
                    model,
                    usage.prompt_tokens,
                    cost,
                    elapsed_ms,
                )
                return EmbeddingResponse(
                    vector=raw.data[0].embedding,
                    model=model,
                    input_tokens=usage.prompt_tokens,
                    cost_usd=cost,
                )
            except RETRYABLE_EXCEPTIONS as exc:
                last_exception = exc
                delay = self._backoff_delay(attempt)
                logger.warning(
                    "Embedding attempt %d/%d failed (%s). Retrying in %.1fs...",
                    attempt,
                    self.max_retries,
                    type(exc).__name__,
                    delay,
                )
                time.sleep(delay)

        raise last_exception  # type: ignore[misc]

    @staticmethod
    def calculate_cost(
        input_tokens: int,
        output_tokens: int,
        model: str = DEFAULT_MODEL,
    ) -> float:
        """
        Calculate the USD cost for a given token count and model.

        Args:
            input_tokens: Number of prompt tokens.
            output_tokens: Number of completion tokens.
            model: Model name.

        Returns:
            Cost in USD (float).
        """
        pricing = MODEL_PRICING.get(model)
        if pricing is None:
            logger.warning("Unknown model %r for pricing, defaulting to gpt-4o", model)
            pricing = MODEL_PRICING[DEFAULT_MODEL]

        cost = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000
        return round(cost, 8)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _request_with_retry(
        self,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """Execute a chat completion with exponential-backoff retry."""
        last_exception = None
        start = time.monotonic()

        for attempt in range(1, self.max_retries + 1):
            try:
                raw = self._client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                elapsed_ms = (time.monotonic() - start) * 1000
                choice = raw.choices[0]
                usage = raw.usage

                cost = self.calculate_cost(
                    usage.prompt_tokens, usage.completion_tokens, model
                )

                response = LLMResponse(
                    content=choice.message.content or "",
                    model=model,
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                    cost_usd=cost,
                    finish_reason=choice.finish_reason or "unknown",
                    latency_ms=elapsed_ms,
                )

                self.usage.record(response)

                logger.info(
                    "LLM response: model=%s in=%d out=%d cost=$%.6f latency=%.0fms reason=%s",
                    model,
                    usage.prompt_tokens,
                    usage.completion_tokens,
                    cost,
                    elapsed_ms,
                    choice.finish_reason,
                )
                return response

            except RETRYABLE_EXCEPTIONS as exc:
                last_exception = exc
                delay = self._backoff_delay(attempt)
                logger.warning(
                    "Attempt %d/%d failed (%s). Retrying in %.1fs...",
                    attempt,
                    self.max_retries,
                    type(exc).__name__,
                    delay,
                )
                self.usage.errors.append(
                    {
                        "attempt": attempt,
                        "error": str(exc),
                        "type": type(exc).__name__,
                    }
                )
                time.sleep(delay)

        raise last_exception  # type: ignore[misc]

    def _backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with a cap."""
        delay = min(RETRY_BASE_DELAY * (2 ** (attempt - 1)), RETRY_MAX_DELAY)
        return delay
