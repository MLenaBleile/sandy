"""Tests for the Reuben agent.

Reference: PROMPTS.md Prompt 10
"""

import json
import math
import random
import textwrap
from unittest.mock import AsyncMock, MagicMock

import pytest

from sandwich.agent.forager import Forager, ForagerConfig
from sandwich.agent.reuben import (
    Reuben,
    Session,
    VOICE_SESSION_START,
    VOICE_SESSION_END,
    VOICE_NO_CANDIDATES,
)
from sandwich.agent.state_machine import AgentState
from sandwich.config import SandwichConfig
from sandwich.db.corpus import SandwichCorpus
from sandwich.sources.base import ContentSource, SourceResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_embedding(seed: int, dim: int = 32) -> list[float]:
    rng = random.Random(seed)
    raw = [rng.gauss(0, 1) for _ in range(dim)]
    norm = math.sqrt(sum(x * x for x in raw))
    return [x / norm for x in raw]


GOOD_CONTENT = textwrap.dedent("""\
    The squeeze theorem, also known as the sandwich theorem, is a fundamental
    result in mathematical analysis. It provides a method for evaluating the
    limit of a function by bounding it between two other functions whose limits
    are already known.

    Formally, suppose that for all x in some interval containing c (except
    possibly at c itself), we have g(x) <= f(x) <= h(x). If both g(x) and h(x)
    approach the same limit L as x approaches c, then f(x) must also approach L.

    This theorem is particularly useful in situations where direct computation of
    a limit is difficult or impossible. The applications extend beyond elementary
    calculus into real analysis and probability theory.
""")

SHORT_CONTENT = "Too short."

GOOD_IDENTIFIER_RESPONSE = json.dumps({
    "candidates": [
        {
            "bread_top": "Upper bound function g(x)",
            "bread_bottom": "Lower bound function h(x)",
            "filling": "Target function f(x)",
            "structure_type": "bound",
            "confidence": 0.95,
            "rationale": "Perfect sandwich.",
        }
    ],
    "no_sandwich_reason": None,
})

GOOD_ASSEMBLER_RESPONSE = json.dumps({
    "name": "The Squeeze",
    "description": "f(x) trapped between bounds converging to L.",
    "containment_argument": "f(x) constrained by g(x) above and h(x) below.",
    "reuben_commentary": "A perfect sandwich. The filling does not choose. Nourishing.",
})

GOOD_VALIDATOR_RESPONSE = json.dumps({
    "bread_compat_score": 0.90,
    "containment_score": 0.95,
    "specificity_score": 0.85,
    "rationale": "Perfect bound structure.",
})

NO_CANDIDATES_RESPONSE = json.dumps({
    "candidates": [],
    "no_sandwich_reason": "No structure here.",
})


class GoodMockSource(ContentSource):
    """Always returns good content."""
    name = "mock_wiki"
    tier = 1
    rate_limiter = None

    async def fetch(self, query=None):
        return SourceResult(
            content=GOOD_CONTENT,
            url="https://example.com/squeeze",
            title="Squeeze Theorem",
            content_type="text",
            metadata={"source": "mock_wiki"},
        )

    async def fetch_random(self):
        return await self.fetch()


class ShortMockSource(ContentSource):
    """Always returns content too short for preprocessing."""
    name = "mock_short"
    tier = 1
    rate_limiter = None

    async def fetch(self, query=None):
        return SourceResult(content=SHORT_CONTENT, metadata={})

    async def fetch_random(self):
        return await self.fetch()


def _make_good_llm() -> AsyncMock:
    """LLM that returns valid responses for all pipeline stages."""
    llm = AsyncMock()
    llm.generate_curiosity = AsyncMock(return_value="squeeze theorem")
    llm.identify_ingredients = AsyncMock(return_value=GOOD_IDENTIFIER_RESPONSE)
    llm.assemble_sandwich = AsyncMock(return_value=GOOD_ASSEMBLER_RESPONSE)
    llm.raw_call = AsyncMock(return_value=GOOD_VALIDATOR_RESPONSE)
    return llm


def _make_failing_llm() -> AsyncMock:
    """LLM that returns no candidates (preprocessing passes but identification fails)."""
    llm = AsyncMock()
    llm.generate_curiosity = AsyncMock(return_value="random topic")
    llm.identify_ingredients = AsyncMock(return_value=NO_CANDIDATES_RESPONSE)
    llm.assemble_sandwich = AsyncMock(return_value=GOOD_ASSEMBLER_RESPONSE)
    llm.raw_call = AsyncMock(return_value=GOOD_VALIDATOR_RESPONSE)
    return llm


def _make_mock_embeddings(dim: int = 32) -> AsyncMock:
    async def _embed_batch(texts):
        return [_make_embedding(seed=hash(t) % 10000, dim=dim) for t in texts]

    emb = AsyncMock()
    emb.embed_single = AsyncMock(
        side_effect=lambda t: _make_embedding(seed=hash(t) % 10000, dim=dim)
    )
    emb.embed_batch = AsyncMock(side_effect=_embed_batch)
    return emb


def _make_reuben(
    source: ContentSource,
    llm: AsyncMock,
    max_patience: int = 5,
) -> tuple[Reuben, list[str]]:
    """Create a Reuben with captured messages."""
    messages = []
    config = SandwichConfig()
    config.foraging.max_patience = max_patience

    forager = Forager(
        sources={1: [source]},
        llm=llm,
        config=ForagerConfig(max_patience=max_patience),
    )

    reuben = Reuben(
        config=config,
        llm=llm,
        embeddings=_make_mock_embeddings(),
        forager=forager,
        emit_fn=messages.append,
    )
    return reuben, messages


# ===================================================================
# test_session_lifecycle
# ===================================================================

class TestSessionLifecycle:
    """Verify session creation and teardown."""

    @pytest.mark.asyncio
    async def test_session_lifecycle(self):
        llm = _make_good_llm()
        reuben, messages = _make_reuben(GoodMockSource(), llm)

        session = await reuben.run(max_sandwiches=1)

        assert session is not None
        assert session.started_at is not None
        assert session.ended_at is not None
        assert session.ended_at >= session.started_at
        assert session.sandwiches_made == 1
        assert session.foraging_attempts >= 1


# ===================================================================
# test_three_sandwiches
# ===================================================================

class TestThreeSandwiches:
    """Verify Reuben can make exactly N sandwiches."""

    @pytest.mark.asyncio
    async def test_three_sandwiches(self):
        llm = _make_good_llm()
        reuben, messages = _make_reuben(GoodMockSource(), llm)

        session = await reuben.run(max_sandwiches=3)

        assert session.sandwiches_made == 3
        assert len(session.sandwiches) == 3

        # All sandwiches should be linked to the session
        for s in session.sandwiches:
            assert s.assembled.name  # Has a name


# ===================================================================
# test_patience_exhaustion
# ===================================================================

class TestPatienceExhaustion:
    """Verify session ends after patience is exhausted."""

    @pytest.mark.asyncio
    async def test_patience_exhaustion(self):
        llm = _make_failing_llm()
        reuben, messages = _make_reuben(GoodMockSource(), llm, max_patience=3)

        session = await reuben.run()

        assert session.sandwiches_made == 0
        assert session.foraging_attempts >= 3
        assert reuben.patience <= 0


# ===================================================================
# test_reuben_voice
# ===================================================================

class TestReubenVoice:
    """Verify Reuben emits messages with appropriate tone."""

    @pytest.mark.asyncio
    async def test_reuben_voice(self):
        llm = _make_good_llm()
        reuben, messages = _make_reuben(GoodMockSource(), llm)

        await reuben.run(max_sandwiches=1)

        # Session start message should be present
        assert any("morning" in m.lower() or "bread" in m.lower() for m in messages), (
            f"No session start message found in: {messages}"
        )

        # Session end message should be present
        assert any("rest" in m.lower() or "patient" in m.lower() for m in messages), (
            f"No session end message found in: {messages}"
        )

        # No complaints
        complaint_phrases = ["i wish", "unfortunately", "i can't", "frustrating", "annoying"]
        for msg in messages:
            msg_lower = msg.lower()
            for phrase in complaint_phrases:
                assert phrase not in msg_lower, (
                    f"Found complaint '{phrase}' in message: {msg}"
                )


# ===================================================================
# test_state_machine_end_state
# ===================================================================

class TestStateMachineEndState:
    """Verify state machine reaches IDLE or SESSION_END after run."""

    @pytest.mark.asyncio
    async def test_ends_in_valid_state(self):
        llm = _make_good_llm()
        reuben, messages = _make_reuben(GoodMockSource(), llm)

        await reuben.run(max_sandwiches=1)

        assert reuben.state_machine.current_state in (
            AgentState.IDLE,
            AgentState.SESSION_END,
        )
