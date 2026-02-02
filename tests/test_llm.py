"""Tests for error taxonomy, retry logic, and embedding caching.

Prompt 2 required tests:
- test_retry_exponential_backoff: verify delays increase exponentially
- test_retry_max_attempts: verify gives up after max retries
- test_error_classification: verify each error type routes correctly
- test_embedding_caching: verify cache hits don't call API
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sandwich.errors.exceptions import (
    ContentError,
    FatalError,
    ParseError,
    RetryableError,
    SandwichError,
)
from sandwich.llm.embeddings import OpenAIEmbeddingService
from sandwich.llm.retry import (
    RetryConfig,
    _extract_json,
    parse_with_recovery,
    with_retry,
)


# ---------------------------------------------------------------------------
# Error taxonomy tests
# ---------------------------------------------------------------------------


class TestErrorTaxonomy:
    """Verify the error class hierarchy and attributes."""

    def test_base_error(self):
        err = SandwichError("something broke", context={"key": "val"})
        assert str(err) == "something broke"
        assert err.context == {"key": "val"}

    def test_retryable_error(self):
        err = RetryableError("rate limited", reason="rate_limit")
        assert isinstance(err, SandwichError)
        assert err.reason == "rate_limit"

    def test_content_error(self):
        err = ContentError("too short", reason="too_short")
        assert isinstance(err, SandwichError)
        assert err.reason == "too_short"

    def test_parse_error(self):
        err = ParseError("bad json", raw_output="{broken")
        assert isinstance(err, SandwichError)
        assert err.raw_output == "{broken"

    def test_fatal_error(self):
        err = FatalError("db down", reason="database_down")
        assert isinstance(err, SandwichError)
        assert err.reason == "database_down"


# ---------------------------------------------------------------------------
# Error classification tests
# ---------------------------------------------------------------------------


class TestErrorClassification:
    """Verify each error type routes correctly through isinstance checks."""

    def test_error_classification(self):
        errors = [
            RetryableError("rate limit", reason="rate_limit"),
            RetryableError("network error", reason="network"),
            RetryableError("timed out", reason="timeout"),
            ContentError("too short", reason="too_short"),
            ContentError("not english", reason="non_english"),
            ContentError("low quality", reason="low_quality"),
            ContentError("seen before", reason="duplicate"),
            ParseError("bad json"),
            FatalError("db down", reason="database_down"),
            FatalError("bad config", reason="config_error"),
            FatalError("bad auth", reason="auth_error"),
        ]

        for err in errors:
            assert isinstance(err, SandwichError)

        # Retryable errors
        retryable = [e for e in errors if isinstance(e, RetryableError)]
        assert len(retryable) == 3
        assert {e.reason for e in retryable} == {"rate_limit", "network", "timeout"}

        # Content errors
        content = [e for e in errors if isinstance(e, ContentError)]
        assert len(content) == 4
        assert {e.reason for e in content} == {
            "too_short",
            "non_english",
            "low_quality",
            "duplicate",
        }

        # Parse errors
        parse = [e for e in errors if isinstance(e, ParseError)]
        assert len(parse) == 1

        # Fatal errors
        fatal = [e for e in errors if isinstance(e, FatalError)]
        assert len(fatal) == 3
        assert {e.reason for e in fatal} == {
            "database_down",
            "config_error",
            "auth_error",
        }


# ---------------------------------------------------------------------------
# Retry logic tests
# ---------------------------------------------------------------------------


class TestRetryExponentialBackoff:
    """Verify delays increase exponentially."""

    @pytest.mark.asyncio
    async def test_retry_exponential_backoff(self):
        """Delays should roughly follow base_delay * exponential_base^attempt."""
        call_count = 0
        sleep_durations: list[float] = []

        async def failing_fn():
            nonlocal call_count
            call_count += 1
            raise RetryableError("fail", reason="network")

        config = RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=100.0,
            exponential_base=2.0,
            jitter=False,  # Disable jitter for predictable delays
        )

        with patch("sandwich.llm.retry.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with pytest.raises(RetryableError):
                await with_retry(failing_fn, config=config)

            # Should have slept 3 times (attempts 0, 1, 2 fail; no sleep after last)
            assert mock_sleep.call_count == 3
            sleep_durations = [call.args[0] for call in mock_sleep.call_args_list]

            # Without jitter: delays should be 1.0, 2.0, 4.0
            assert sleep_durations[0] == pytest.approx(1.0)
            assert sleep_durations[1] == pytest.approx(2.0)
            assert sleep_durations[2] == pytest.approx(4.0)

        # 1 initial + 3 retries = 4 total calls
        assert call_count == 4

    @pytest.mark.asyncio
    async def test_retry_with_jitter(self):
        """With jitter enabled, delays should be randomized but bounded."""
        config = RetryConfig(
            max_retries=2,
            base_delay=1.0,
            max_delay=100.0,
            exponential_base=2.0,
            jitter=True,
        )

        async def failing_fn():
            raise RetryableError("fail", reason="network")

        with patch("sandwich.llm.retry.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with pytest.raises(RetryableError):
                await with_retry(failing_fn, config=config)

            # With jitter, delay = base * (0.5 + rand()) so range is [0.5*base, 1.5*base]
            for i, call in enumerate(mock_sleep.call_args_list):
                base = 1.0 * (2.0**i)
                assert 0.5 * base <= call.args[0] <= 1.5 * base


class TestRetryMaxAttempts:
    """Verify gives up after max retries."""

    @pytest.mark.asyncio
    async def test_retry_max_attempts(self):
        call_count = 0

        async def failing_fn():
            nonlocal call_count
            call_count += 1
            raise RetryableError("always fails", reason="timeout")

        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=False)

        with patch("sandwich.llm.retry.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RetryableError, match="always fails"):
                await with_retry(failing_fn, config=config)

        # 1 initial + 2 retries = 3 total
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_success_on_second_attempt(self):
        """Should return successfully if a retry succeeds."""
        call_count = 0

        async def sometimes_fails():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RetryableError("transient", reason="network")
            return "success"

        config = RetryConfig(max_retries=3, base_delay=0.01, jitter=False)

        with patch("sandwich.llm.retry.asyncio.sleep", new_callable=AsyncMock):
            result = await with_retry(sometimes_fails, config=config)

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_fatal_error_not_retried(self):
        """FatalError should propagate immediately without retry."""
        call_count = 0

        async def fatal_fn():
            nonlocal call_count
            call_count += 1
            raise FatalError("db down", reason="database_down")

        config = RetryConfig(max_retries=3, base_delay=0.01)

        with pytest.raises(FatalError, match="db down"):
            await with_retry(fatal_fn, config=config)

        assert call_count == 1  # No retries


# ---------------------------------------------------------------------------
# JSON extraction / parse_with_recovery tests
# ---------------------------------------------------------------------------


class TestJsonExtraction:
    """Test _extract_json helper."""

    def test_plain_json(self):
        result = _extract_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_in_code_fence(self):
        text = '```json\n{"key": "value"}\n```'
        result = _extract_json(text)
        assert result == {"key": "value"}

    def test_json_surrounded_by_prose(self):
        text = 'Here is the result:\n{"key": "value"}\nThat is the answer.'
        result = _extract_json(text)
        assert result == {"key": "value"}

    def test_invalid_json_raises(self):
        with pytest.raises(ParseError):
            _extract_json("this is not json at all")


class TestParseWithRecovery:
    @pytest.mark.asyncio
    async def test_parse_success(self):
        result = await parse_with_recovery(
            '{"name": "test", "score": 0.8}',
            required_fields=["name", "score"],
        )
        assert result["name"] == "test"
        assert result["score"] == 0.8

    @pytest.mark.asyncio
    async def test_parse_missing_fields_no_retry(self):
        with pytest.raises(ParseError, match="Missing required fields"):
            await parse_with_recovery(
                '{"name": "test"}',
                required_fields=["name", "score"],
            )

    @pytest.mark.asyncio
    async def test_parse_recovery_with_retry(self):
        """Should retry with stricter prompt and succeed."""
        async def mock_llm_call(prompt):
            return '{"name": "test", "score": 0.9}'

        result = await parse_with_recovery(
            '{"name": "test"}',  # missing 'score'
            required_fields=["name", "score"],
            llm_call=mock_llm_call,
            retry_prompt="Please include the score field.",
        )
        assert result["score"] == 0.9


# ---------------------------------------------------------------------------
# Embedding caching tests
# ---------------------------------------------------------------------------


class TestEmbeddingCaching:
    """Verify cache hits don't call API."""

    @pytest.mark.asyncio
    async def test_embedding_caching(self):
        """Second call for the same text should use cache, not API."""
        service = OpenAIEmbeddingService()
        fake_embedding = [0.1] * 1536

        with patch.object(service, "_api_embed", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {
                "embeddings": [fake_embedding],
                "total_tokens": 10,
            }

            # First call — should hit API
            result1 = await service.embed_single("test text")
            assert mock_api.call_count == 1
            assert result1 == fake_embedding

            # Second call — should hit cache
            result2 = await service.embed_single("test text")
            assert mock_api.call_count == 1  # NOT incremented
            assert result2 == fake_embedding

    @pytest.mark.asyncio
    async def test_embedding_batch_caching(self):
        """Batch calls should use cache for previously seen texts."""
        service = OpenAIEmbeddingService()
        emb_a = [0.1] * 1536
        emb_b = [0.2] * 1536
        emb_c = [0.3] * 1536

        with patch.object(service, "_api_embed", new_callable=AsyncMock) as mock_api:
            # First batch: all uncached
            mock_api.return_value = {
                "embeddings": [emb_a, emb_b],
                "total_tokens": 20,
            }
            results1 = await service.embed_batch(["text_a", "text_b"])
            assert results1 == [emb_a, emb_b]
            assert mock_api.call_count == 1

            # Second batch: text_a cached, text_c uncached
            mock_api.return_value = {
                "embeddings": [emb_c],
                "total_tokens": 10,
            }
            results2 = await service.embed_batch(["text_a", "text_c"])
            assert results2 == [emb_a, emb_c]
            assert mock_api.call_count == 2

            # Verify only text_c was sent to API
            last_call_texts = mock_api.call_args[0][0]
            assert last_call_texts == ["text_c"]

    @pytest.mark.asyncio
    async def test_embedding_cache_eviction(self):
        """Cache should evict oldest entry when full."""
        service = OpenAIEmbeddingService(max_cache_size=2)

        with patch.object(service, "_api_embed", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {
                "embeddings": [[0.1] * 1536],
                "total_tokens": 5,
            }

            await service.embed_single("text1")
            await service.embed_single("text2")
            await service.embed_single("text3")  # Should evict text1

            assert mock_api.call_count == 3

            # text2 should still be cached
            await service.embed_single("text2")
            assert mock_api.call_count == 3  # cache hit

            # text1 should have been evicted
            await service.embed_single("text1")
            assert mock_api.call_count == 4  # cache miss, re-fetched
