"""
Tests for the OpenAI client wrapper (apps.llm_service.client).

All tests mock the OpenAI API — no real API calls are made.
"""
import pytest
from unittest.mock import MagicMock, patch

from openai import APIConnectionError, APITimeoutError, RateLimitError

from apps.llm_service.client import (
    DEFAULT_MODEL,
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
    MODEL_PRICING,
    VALIDATION_MODEL,
    EmbeddingResponse,
    LLMResponse,
    OpenAIClient,
    UsageStats,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _mock_chat_completion(
    content="Test response",
    model="gpt-4o",
    prompt_tokens=100,
    completion_tokens=50,
    total_tokens=150,
    finish_reason="stop",
):
    """Build a mock ChatCompletion response object."""
    choice = MagicMock()
    choice.message.content = content
    choice.finish_reason = finish_reason

    usage = MagicMock()
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = completion_tokens
    usage.total_tokens = total_tokens

    response = MagicMock()
    response.choices = [choice]
    response.usage = usage
    return response


def _mock_embedding_response(vector=None, prompt_tokens=10):
    """Build a mock Embeddings response object."""
    if vector is None:
        vector = [0.1] * EMBEDDING_DIMENSIONS

    data_item = MagicMock()
    data_item.embedding = vector

    usage = MagicMock()
    usage.prompt_tokens = prompt_tokens

    response = MagicMock()
    response.data = [data_item]
    response.usage = usage
    return response


@pytest.fixture
def mock_openai_class():
    """Patch the OpenAI class so no real client is created."""
    with patch("apps.llm_service.client.OpenAI") as mock_cls:
        yield mock_cls


@pytest.fixture
def client(mock_openai_class):
    """Create an OpenAIClient with a mocked backend."""
    instance = mock_openai_class.return_value
    instance.chat.completions.create.return_value = _mock_chat_completion()
    instance.embeddings.create.return_value = _mock_embedding_response()
    return OpenAIClient(api_key="test-key-12345")


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------


class TestOpenAIClientInit:
    """Tests for client initialization and configuration."""

    def test_raises_when_no_api_key(self, mock_openai_class):
        """Client should raise ValueError when no API key is provided."""
        with patch("apps.llm_service.client.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = ""
            with pytest.raises(ValueError, match="API key"):
                OpenAIClient(api_key="")

    def test_accepts_explicit_api_key(self, mock_openai_class):
        """Client should accept an explicitly provided API key."""
        client = OpenAIClient(api_key="sk-test-explicit")
        mock_openai_class.assert_called_once()
        assert client.default_model == DEFAULT_MODEL

    def test_default_model(self, client):
        """Client should default to gpt-4o model."""
        assert client.default_model == DEFAULT_MODEL

    def test_custom_model(self, mock_openai_class):
        """Client should accept a custom default model."""
        client = OpenAIClient(api_key="test-key", default_model="gpt-4o-mini")
        assert client.default_model == "gpt-4o-mini"

    def test_usage_stats_initialized(self, client):
        """Client should start with empty usage stats."""
        assert isinstance(client.usage, UsageStats)
        assert client.usage.total_input_tokens == 0
        assert client.usage.total_cost_usd == 0.0
        assert client.usage.request_count == 0


# ---------------------------------------------------------------------------
# send_message tests
# ---------------------------------------------------------------------------


class TestSendMessage:
    """Tests for the send_message method."""

    def test_basic_response(self, client, mock_openai_class):
        """send_message should return a valid LLMResponse."""
        result = client.send_message(
            system_prompt="You are a TRIZ expert.",
            messages=[{"role": "user", "content": "Hello"}],
        )

        assert isinstance(result, LLMResponse)
        assert result.content == "Test response"
        assert result.model == DEFAULT_MODEL
        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert result.total_tokens == 150
        assert result.finish_reason == "stop"
        assert result.cost_usd > 0
        assert result.latency_ms >= 0

    def test_system_prompt_prepended(self, client, mock_openai_class):
        """The system prompt should be added as the first message."""
        client.send_message(
            system_prompt="System instructions",
            messages=[{"role": "user", "content": "Hello"}],
        )

        call_args = mock_openai_class.return_value.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "System instructions"
        assert messages[1]["role"] == "user"

    def test_custom_model_override(self, client, mock_openai_class):
        """send_message should use the model override when provided."""
        mock_openai_class.return_value.chat.completions.create.return_value = (
            _mock_chat_completion(model="gpt-4o-mini")
        )

        result = client.send_message(
            system_prompt="Test",
            messages=[{"role": "user", "content": "Test"}],
            model="gpt-4o-mini",
        )

        call_args = mock_openai_class.return_value.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-4o-mini"

    def test_custom_temperature(self, client, mock_openai_class):
        """Temperature should be passed through to the API."""
        client.send_message(
            system_prompt="Test",
            messages=[{"role": "user", "content": "Test"}],
            temperature=0.3,
        )

        call_args = mock_openai_class.return_value.chat.completions.create.call_args
        assert call_args.kwargs["temperature"] == 0.3

    def test_custom_max_tokens(self, client, mock_openai_class):
        """max_tokens should be passed through to the API."""
        client.send_message(
            system_prompt="Test",
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=2048,
        )

        call_args = mock_openai_class.return_value.chat.completions.create.call_args
        assert call_args.kwargs["max_tokens"] == 2048

    def test_usage_stats_recorded(self, client):
        """Usage stats should be updated after each call."""
        client.send_message(
            system_prompt="Test",
            messages=[{"role": "user", "content": "Test"}],
        )

        assert client.usage.request_count == 1
        assert client.usage.total_input_tokens == 100
        assert client.usage.total_output_tokens == 50
        assert client.usage.total_cost_usd > 0


# ---------------------------------------------------------------------------
# send_validation tests
# ---------------------------------------------------------------------------


class TestSendValidation:
    """Tests for the send_validation convenience method."""

    def test_uses_validation_model(self, client, mock_openai_class):
        """send_validation should use gpt-4o-mini by default."""
        mock_openai_class.return_value.chat.completions.create.return_value = (
            _mock_chat_completion(model=VALIDATION_MODEL, prompt_tokens=50, completion_tokens=20, total_tokens=70)
        )

        result = client.send_validation(
            system_prompt="Validate this.",
            messages=[{"role": "user", "content": "Content to check"}],
        )

        call_args = mock_openai_class.return_value.chat.completions.create.call_args
        assert call_args.kwargs["model"] == VALIDATION_MODEL
        assert call_args.kwargs["temperature"] == 0.3

    def test_validation_max_tokens(self, client, mock_openai_class):
        """send_validation should default to 2048 max_tokens."""
        mock_openai_class.return_value.chat.completions.create.return_value = (
            _mock_chat_completion()
        )

        client.send_validation(
            system_prompt="Test",
            messages=[{"role": "user", "content": "Test"}],
        )

        call_args = mock_openai_class.return_value.chat.completions.create.call_args
        assert call_args.kwargs["max_tokens"] == 2048


# ---------------------------------------------------------------------------
# create_embedding tests
# ---------------------------------------------------------------------------


class TestCreateEmbedding:
    """Tests for the create_embedding method."""

    def test_basic_embedding(self, client, mock_openai_class):
        """create_embedding should return a valid EmbeddingResponse."""
        result = client.create_embedding("Test text for embedding")

        assert isinstance(result, EmbeddingResponse)
        assert len(result.vector) == EMBEDDING_DIMENSIONS
        assert result.model == EMBEDDING_MODEL
        assert result.input_tokens == 10
        assert result.cost_usd >= 0

    def test_embedding_api_called(self, client, mock_openai_class):
        """create_embedding should call the embeddings API with correct params."""
        client.create_embedding("Test text")

        call_args = mock_openai_class.return_value.embeddings.create.call_args
        assert call_args.kwargs["input"] == "Test text"
        assert call_args.kwargs["model"] == EMBEDDING_MODEL
        assert call_args.kwargs["dimensions"] == EMBEDDING_DIMENSIONS


# ---------------------------------------------------------------------------
# Retry logic tests
# ---------------------------------------------------------------------------


class TestRetryLogic:
    """Tests for the exponential backoff retry mechanism."""

    def test_retries_on_rate_limit(self, mock_openai_class):
        """Client should retry on RateLimitError."""
        instance = mock_openai_class.return_value
        mock_response = _mock_chat_completion()

        # Fail once, then succeed
        instance.chat.completions.create.side_effect = [
            RateLimitError(
                message="Rate limit exceeded",
                response=MagicMock(status_code=429),
                body=None,
            ),
            mock_response,
        ]

        with patch("apps.llm_service.client.time.sleep"):
            client = OpenAIClient(api_key="test-key")
            result = client.send_message(
                system_prompt="Test",
                messages=[{"role": "user", "content": "Test"}],
            )

        assert result.content == "Test response"
        assert instance.chat.completions.create.call_count == 2

    def test_retries_on_timeout(self, mock_openai_class):
        """Client should retry on APITimeoutError."""
        instance = mock_openai_class.return_value
        mock_response = _mock_chat_completion()

        instance.chat.completions.create.side_effect = [
            APITimeoutError(request=MagicMock()),
            mock_response,
        ]

        with patch("apps.llm_service.client.time.sleep"):
            client = OpenAIClient(api_key="test-key")
            result = client.send_message(
                system_prompt="Test",
                messages=[{"role": "user", "content": "Test"}],
            )

        assert result.content == "Test response"
        assert instance.chat.completions.create.call_count == 2

    def test_retries_on_connection_error(self, mock_openai_class):
        """Client should retry on APIConnectionError."""
        instance = mock_openai_class.return_value
        mock_response = _mock_chat_completion()

        instance.chat.completions.create.side_effect = [
            APIConnectionError(request=MagicMock()),
            mock_response,
        ]

        with patch("apps.llm_service.client.time.sleep"):
            client = OpenAIClient(api_key="test-key")
            result = client.send_message(
                system_prompt="Test",
                messages=[{"role": "user", "content": "Test"}],
            )

        assert result.content == "Test response"

    def test_raises_after_max_retries(self, mock_openai_class):
        """Client should raise after exhausting all retries."""
        instance = mock_openai_class.return_value
        instance.chat.completions.create.side_effect = RateLimitError(
            message="Rate limit exceeded",
            response=MagicMock(status_code=429),
            body=None,
        )

        with patch("apps.llm_service.client.time.sleep"):
            client = OpenAIClient(api_key="test-key", max_retries=3)
            with pytest.raises(RateLimitError):
                client.send_message(
                    system_prompt="Test",
                    messages=[{"role": "user", "content": "Test"}],
                )

        assert instance.chat.completions.create.call_count == 3

    def test_errors_recorded_in_usage(self, mock_openai_class):
        """Retry errors should be recorded in usage stats."""
        instance = mock_openai_class.return_value
        mock_response = _mock_chat_completion()

        instance.chat.completions.create.side_effect = [
            RateLimitError(
                message="Rate limit exceeded",
                response=MagicMock(status_code=429),
                body=None,
            ),
            mock_response,
        ]

        with patch("apps.llm_service.client.time.sleep"):
            client = OpenAIClient(api_key="test-key")
            client.send_message(
                system_prompt="Test",
                messages=[{"role": "user", "content": "Test"}],
            )

        assert len(client.usage.errors) == 1
        assert client.usage.errors[0]["type"] == "RateLimitError"

    def test_embedding_retries_on_error(self, mock_openai_class):
        """create_embedding should retry on transient errors."""
        instance = mock_openai_class.return_value
        mock_resp = _mock_embedding_response()

        instance.embeddings.create.side_effect = [
            APITimeoutError(request=MagicMock()),
            mock_resp,
        ]

        with patch("apps.llm_service.client.time.sleep"):
            client = OpenAIClient(api_key="test-key")
            result = client.create_embedding("Test text")

        assert isinstance(result, EmbeddingResponse)
        assert instance.embeddings.create.call_count == 2


# ---------------------------------------------------------------------------
# calculate_cost tests
# ---------------------------------------------------------------------------


class TestCalculateCost:
    """Tests for the cost calculation utility."""

    def test_gpt4o_cost(self):
        """Cost for gpt-4o should use correct pricing."""
        cost = OpenAIClient.calculate_cost(
            input_tokens=1000, output_tokens=500, model="gpt-4o"
        )
        # 1000 * 2.50 / 1M + 500 * 10.00 / 1M = 0.0025 + 0.005 = 0.0075
        assert abs(cost - 0.0075) < 1e-6

    def test_gpt4o_mini_cost(self):
        """Cost for gpt-4o-mini should use cheaper pricing."""
        cost = OpenAIClient.calculate_cost(
            input_tokens=1000, output_tokens=500, model="gpt-4o-mini"
        )
        # 1000 * 0.15 / 1M + 500 * 0.60 / 1M = 0.00015 + 0.0003 = 0.00045
        assert abs(cost - 0.00045) < 1e-6

    def test_embedding_cost(self):
        """Cost for embeddings should be input-only."""
        cost = OpenAIClient.calculate_cost(
            input_tokens=1000, output_tokens=0, model="text-embedding-3-small"
        )
        # 1000 * 0.02 / 1M = 0.00002
        assert abs(cost - 0.00002) < 1e-6

    def test_zero_tokens(self):
        """Cost should be zero for zero tokens."""
        cost = OpenAIClient.calculate_cost(0, 0, "gpt-4o")
        assert cost == 0.0

    def test_unknown_model_defaults_to_gpt4o(self):
        """Unknown model should fall back to gpt-4o pricing."""
        cost_unknown = OpenAIClient.calculate_cost(1000, 500, "gpt-future-model")
        cost_gpt4o = OpenAIClient.calculate_cost(1000, 500, "gpt-4o")
        assert cost_unknown == cost_gpt4o

    def test_all_models_have_pricing(self):
        """All models in MODEL_PRICING should have input and output keys."""
        for model, pricing in MODEL_PRICING.items():
            assert "input" in pricing, f"{model} missing 'input' price"
            assert "output" in pricing, f"{model} missing 'output' price"


# ---------------------------------------------------------------------------
# UsageStats tests
# ---------------------------------------------------------------------------


class TestUsageStats:
    """Tests for the UsageStats dataclass."""

    def test_record_accumulates(self):
        """Usage stats should accumulate across multiple records."""
        stats = UsageStats()
        response1 = LLMResponse(
            content="r1", model="gpt-4o", input_tokens=100,
            output_tokens=50, total_tokens=150, cost_usd=0.01,
            finish_reason="stop", latency_ms=500,
        )
        response2 = LLMResponse(
            content="r2", model="gpt-4o", input_tokens=200,
            output_tokens=100, total_tokens=300, cost_usd=0.02,
            finish_reason="stop", latency_ms=700,
        )

        stats.record(response1)
        stats.record(response2)

        assert stats.total_input_tokens == 300
        assert stats.total_output_tokens == 150
        assert abs(stats.total_cost_usd - 0.03) < 1e-8
        assert stats.request_count == 2
