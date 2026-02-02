"""OpenAI embedding service with in-memory caching.

Reference: SPEC.md Sections 7.1, 7.2
"""

import logging
from typing import Optional

import openai

from sandwich.config import LLMConfig
from sandwich.errors.exceptions import FatalError, RetryableError
from sandwich.llm.interface import EmbeddingService
from sandwich.llm.retry import RetryConfig, with_retry
from sandwich.observability.logging import NullObserver, hash_prompt

logger = logging.getLogger(__name__)


class OpenAIEmbeddingService(EmbeddingService):
    """EmbeddingService backed by the OpenAI embeddings API.

    Includes an in-memory cache keyed by input text to avoid redundant
    API calls for repeated content.
    """

    def __init__(
        self,
        config: LLMConfig | None = None,
        observer: object | None = None,
        retry_config: RetryConfig | None = None,
        max_cache_size: int = 10_000,
    ):
        self.config = config or LLMConfig()
        self.observer = observer or NullObserver()
        self.retry_config = retry_config or RetryConfig()
        self.max_cache_size = max_cache_size
        self._client_instance: openai.OpenAI | None = None
        self._cache: dict[str, list[float]] = {}

    @property
    def _client(self) -> openai.OpenAI:
        """Lazily initialize the OpenAI client (avoids API key check at import time)."""
        if self._client_instance is None:
            self._client_instance = openai.OpenAI()
        return self._client_instance

    def _cache_key(self, text: str) -> str:
        return text.strip()

    def _put_cache(self, text: str, embedding: list[float]) -> None:
        key = self._cache_key(text)
        if len(self._cache) >= self.max_cache_size:
            # Evict oldest entry (first inserted)
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        self._cache[key] = embedding

    def _get_cache(self, text: str) -> Optional[list[float]]:
        return self._cache.get(self._cache_key(text))

    async def embed_single(self, text: str) -> list[float]:
        cached = self._get_cache(text)
        if cached is not None:
            return cached

        prompt_h = hash_prompt(text)
        start = self.observer.on_call_start("embedding", prompt_h)

        error_str: Optional[str] = None
        total_tokens = 0
        try:
            result = await self._api_embed([text])
            total_tokens = result["total_tokens"]
            embedding = result["embeddings"][0]
            self._put_cache(text, embedding)
            return embedding
        except Exception as e:
            error_str = str(e)
            raise
        finally:
            self.observer.on_call_end(
                component="embedding",
                model=self.config.embedding_model,
                prompt_hash=prompt_h,
                start_time=start,
                input_tokens=total_tokens,
                output_tokens=0,
                error=error_str,
            )

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        # Separate cached from uncached
        results: list[Optional[list[float]]] = [None] * len(texts)
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        for i, text in enumerate(texts):
            cached = self._get_cache(text)
            if cached is not None:
                results[i] = cached
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        if uncached_texts:
            prompt_h = hash_prompt("||".join(uncached_texts))
            start = self.observer.on_call_start("embedding_batch", prompt_h)
            error_str: Optional[str] = None
            total_tokens = 0
            try:
                api_result = await self._api_embed(uncached_texts)
                total_tokens = api_result["total_tokens"]
                for idx, embedding in zip(
                    uncached_indices, api_result["embeddings"]
                ):
                    results[idx] = embedding
                    self._put_cache(texts[idx], embedding)
            except Exception as e:
                error_str = str(e)
                raise
            finally:
                self.observer.on_call_end(
                    component="embedding_batch",
                    model=self.config.embedding_model,
                    prompt_hash=prompt_h,
                    start_time=start,
                    input_tokens=total_tokens,
                    output_tokens=0,
                    error=error_str,
                )

        return results  # type: ignore[return-value]

    async def _api_embed(self, texts: list[str]) -> dict:
        """Call the OpenAI embeddings API with retry."""

        async def _do_call() -> dict:
            try:
                response = self._client.embeddings.create(
                    model=self.config.embedding_model,
                    input=texts,
                )
                embeddings = [item.embedding for item in response.data]
                total_tokens = response.usage.total_tokens
                return {"embeddings": embeddings, "total_tokens": total_tokens}
            except openai.RateLimitError as e:
                raise RetryableError(str(e), reason="rate_limit") from e
            except openai.APIConnectionError as e:
                raise RetryableError(str(e), reason="network") from e
            except openai.APITimeoutError as e:
                raise RetryableError(str(e), reason="timeout") from e
            except openai.AuthenticationError as e:
                raise FatalError(str(e), reason="auth_error") from e
            except openai.APIStatusError as e:
                if e.status_code and e.status_code >= 500:
                    raise RetryableError(str(e), reason="network") from e
                raise FatalError(str(e), reason="unknown") from e

        return await with_retry(_do_call, config=self.retry_config)
