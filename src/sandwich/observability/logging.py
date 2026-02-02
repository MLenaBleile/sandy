"""LLM call observer for logging and cost tracking.

Logs all LLM calls to the llm_call_log table, tracking prompt hashes,
latency, token usage, cost, and errors.
"""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Protocol
from uuid import UUID, uuid4

import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)

# Approximate cost per 1K tokens (USD) — Anthropic Claude Sonnet
# These are defaults; actual pricing may vary.
DEFAULT_COST_PER_1K_INPUT = 0.003
DEFAULT_COST_PER_1K_OUTPUT = 0.015

# OpenAI text-embedding-3-small
DEFAULT_EMBEDDING_COST_PER_1K = 0.00002


@dataclass
class LLMCallRecord:
    """A single LLM call record for observability."""

    call_id: UUID = field(default_factory=uuid4)
    component: str = ""  # 'curiosity', 'identifier', 'assembler', 'validator', etc.
    model: str = ""
    prompt_hash: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    error: Optional[str] = None
    session_id: Optional[UUID] = None


class LLMObserver(Protocol):
    """Protocol for observing LLM calls."""

    def on_call_start(self, component: str, prompt_hash: str) -> float:
        """Called before an LLM API call. Returns start_time."""
        ...

    def on_call_end(
        self,
        component: str,
        model: str,
        prompt_hash: str,
        start_time: float,
        input_tokens: int,
        output_tokens: int,
        error: Optional[str] = None,
    ) -> None:
        """Called after an LLM API call completes (success or failure)."""
        ...


class LoggingObserver:
    """Observer that logs LLM calls to the llm_call_log database table."""

    def __init__(
        self,
        connection_string: str,
        session_id: Optional[UUID] = None,
        cost_per_1k_input: float = DEFAULT_COST_PER_1K_INPUT,
        cost_per_1k_output: float = DEFAULT_COST_PER_1K_OUTPUT,
    ):
        self.connection_string = connection_string
        self.session_id = session_id
        self.cost_per_1k_input = cost_per_1k_input
        self.cost_per_1k_output = cost_per_1k_output
        self._conn: Optional[psycopg2.extensions.connection] = None

    @property
    def conn(self) -> psycopg2.extensions.connection:
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(self.connection_string)
            self._conn.autocommit = True
        return self._conn

    def on_call_start(self, component: str, prompt_hash: str) -> float:
        """Record the start time of an LLM call."""
        logger.debug("LLM call starting: component=%s", component)
        return time.monotonic()

    def on_call_end(
        self,
        component: str,
        model: str,
        prompt_hash: str,
        start_time: float,
        input_tokens: int,
        output_tokens: int,
        error: Optional[str] = None,
    ) -> None:
        """Log the completed LLM call to the database."""
        latency_ms = (time.monotonic() - start_time) * 1000
        cost_usd = (
            (input_tokens / 1000) * self.cost_per_1k_input
            + (output_tokens / 1000) * self.cost_per_1k_output
        )

        record = LLMCallRecord(
            component=component,
            model=model,
            prompt_hash=prompt_hash,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            error=error,
            session_id=self.session_id,
        )

        logger.info(
            "LLM call: component=%s model=%s tokens=%d+%d latency=%.0fms cost=$%.6f%s",
            component,
            model,
            input_tokens,
            output_tokens,
            latency_ms,
            cost_usd,
            f" error={error}" if error else "",
        )

        try:
            self._persist(record)
        except Exception:
            logger.exception("Failed to persist LLM call log")

    def _persist(self, record: LLMCallRecord) -> None:
        """Write a call record to the llm_call_log table."""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO llm_call_log (
                        call_id, component, model, prompt_hash,
                        input_tokens, output_tokens, latency_ms,
                        cost_usd, error, session_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        record.call_id,
                        record.component,
                        record.model,
                        record.prompt_hash,
                        record.input_tokens,
                        record.output_tokens,
                        record.latency_ms,
                        record.cost_usd,
                        record.error,
                        record.session_id,
                    ),
                )
        except psycopg2.Error:
            logger.exception("Database error persisting LLM call log")

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None


class NullObserver:
    """No-op observer for use when logging is not needed (e.g., tests)."""

    def on_call_start(self, component: str, prompt_hash: str) -> float:
        return time.monotonic()

    def on_call_end(
        self,
        component: str,
        model: str,
        prompt_hash: str,
        start_time: float,
        input_tokens: int,
        output_tokens: int,
        error: Optional[str] = None,
    ) -> None:
        pass


def hash_prompt(text: str) -> str:
    """Create a short hash of a prompt for deduplication tracking."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]
