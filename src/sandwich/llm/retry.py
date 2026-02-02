"""Retry logic with exponential backoff and jitter.

Reference: SPEC.md Sections 6.1, 6.2
"""

import asyncio
import json
import logging
import random
import re
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

from sandwich.errors.exceptions import FatalError, ParseError, RetryableError

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


DEFAULT_RETRY_CONFIG = RetryConfig()


async def with_retry(
    fn: Callable[..., Any],
    *args: Any,
    config: RetryConfig | None = None,
    **kwargs: Any,
) -> Any:
    """Execute an async function with exponential backoff retry on RetryableError.

    Args:
        fn: Async callable to retry.
        *args: Positional arguments for fn.
        config: Retry configuration. Uses defaults if None.
        **kwargs: Keyword arguments for fn.

    Returns:
        The result of fn.

    Raises:
        RetryableError: If all retries are exhausted.
        FatalError: Immediately, without retry.
    """
    cfg = config or DEFAULT_RETRY_CONFIG
    last_error: Exception | None = None

    for attempt in range(cfg.max_retries + 1):
        try:
            return await fn(*args, **kwargs)
        except FatalError:
            raise
        except RetryableError as e:
            last_error = e
            if attempt == cfg.max_retries:
                logger.error(
                    "All %d retries exhausted for %s: %s",
                    cfg.max_retries,
                    fn.__name__,
                    e,
                )
                raise

            delay = min(
                cfg.base_delay * (cfg.exponential_base**attempt),
                cfg.max_delay,
            )
            if cfg.jitter:
                delay = delay * (0.5 + random.random())

            logger.warning(
                "Retry %d/%d for %s after %.1fs: %s",
                attempt + 1,
                cfg.max_retries,
                fn.__name__,
                delay,
                e,
            )
            await asyncio.sleep(delay)

    # Should not reach here, but just in case
    raise last_error  # type: ignore[misc]


def _extract_json(text: str) -> dict:
    """Extract a JSON object from text that may contain surrounding prose."""
    # Try direct parse first
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON block in markdown code fence
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try to find first { ... } block
    brace_start = text.find("{")
    if brace_start != -1:
        depth = 0
        for i in range(brace_start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[brace_start : i + 1])
                    except json.JSONDecodeError:
                        break

    raise ParseError(
        "Could not extract valid JSON from LLM response",
        raw_output=text,
    )


async def parse_with_recovery(
    raw_text: str,
    required_fields: list[str],
    llm_call: Callable[..., Any] | None = None,
    retry_prompt: str | None = None,
) -> dict:
    """Parse JSON from LLM output with recovery on failure.

    Attempts to extract JSON from the raw text. If the first attempt fails
    or is missing required fields, optionally retries with a stricter prompt.

    Args:
        raw_text: The raw LLM output text.
        required_fields: List of field names that must be present.
        llm_call: Optional async callable to retry with a stricter prompt.
        retry_prompt: Optional stricter prompt for the retry call.

    Returns:
        Parsed dict with all required fields.

    Raises:
        ParseError: If parsing fails after all attempts.
    """
    # Attempt 1: parse the raw text
    try:
        parsed = _extract_json(raw_text)
    except ParseError:
        parsed = None

    if parsed is not None:
        missing = [f for f in required_fields if f not in parsed]
        if not missing:
            return parsed
    else:
        missing = required_fields

    # Attempt 2: retry with stricter prompt if available
    if llm_call and retry_prompt:
        logger.warning(
            "Parse attempt 1 had issues (missing=%s), retrying with stricter prompt",
            missing,
        )
        retry_text = await llm_call(retry_prompt)
        parsed = _extract_json(retry_text)
        missing = [f for f in required_fields if f not in parsed]
        if not missing:
            return parsed
        raise ParseError(
            f"Missing required fields: {missing}",
            raw_output=str(parsed),
        )

    # No retry mechanism — raise with the best info we have
    if parsed is not None:
        raise ParseError(
            f"Missing required fields: {missing}",
            raw_output=str(parsed),
        )
    raise ParseError(
        "Could not extract valid JSON from LLM response",
        raw_output=raw_text,
    )
