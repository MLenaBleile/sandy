"""Tests for the sandwich validator (Prompt 3 - CRITICAL GATE).

Tests 6 sandwiches:
- 3 good sandwiches (expected overall > 0.7)
- 3 bad sandwiches (expected overall < 0.5)

The validator uses hybrid scoring:
  - LLM-judged: bread_compat_score, containment_score
  - Embedding-based: nontrivial_score, novelty_score

We mock both LLM and embedding services so tests run without API keys.
The mock LLM returns scores that a competent LLM would give.
The mock embeddings return vectors designed to exercise the nontrivial check.
"""

import json
import math
from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from sandwich.agent.validator import (
    ValidationConfig,
    ValidationResult,
    _cosine_similarity,
    validate_sandwich,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_embedding(seed: int, dim: int = 1536) -> list[float]:
    """Create a deterministic pseudo-random unit vector for testing.

    Different seeds produce different vectors; same seed always gives the same
    vector. Vectors from distant seeds will have low cosine similarity.
    """
    import hashlib

    raw = []
    for i in range(dim):
        h = hashlib.md5(f"{seed}-{i}".encode()).hexdigest()
        raw.append((int(h[:8], 16) / 0xFFFFFFFF) - 0.5)
    # Normalize to unit length
    norm = math.sqrt(sum(x * x for x in raw))
    return [x / norm for x in raw]


def _make_identical_embedding(base: list[float]) -> list[float]:
    """Return a copy of the base embedding (similarity ~1.0)."""
    return list(base)


def _make_similar_embedding(base: list[float], noise: float = 0.05) -> list[float]:
    """Return a slightly perturbed copy (high similarity)."""
    import hashlib

    result = []
    for i, v in enumerate(base):
        h = hashlib.md5(f"noise-{i}".encode()).hexdigest()
        delta = ((int(h[:8], 16) / 0xFFFFFFFF) - 0.5) * noise
        result.append(v + delta)
    norm = math.sqrt(sum(x * x for x in result))
    return [x / norm for x in result]


class MockLLM:
    """Mock LLM that returns predefined validator JSON responses."""

    def __init__(self, bread_compat: float, containment: float, rationale: str = "Mock evaluation"):
        self.bread_compat = bread_compat
        self.containment = containment
        self.rationale = rationale

    async def raw_call(self, system_prompt: str, user_prompt: str) -> str:
        return json.dumps({
            "bread_compat_score": self.bread_compat,
            "containment_score": self.containment,
            "rationale": self.rationale,
        })


class MockEmbeddingService:
    """Mock embedding service that returns predetermined vectors.

    Maps text -> embedding via a lookup dict. Unknown texts get a random
    embedding seeded by hash of the text.
    """

    def __init__(self, mapping: dict[str, list[float]] | None = None):
        self._mapping = mapping or {}

    def _get_embedding(self, text: str) -> list[float]:
        if text in self._mapping:
            return self._mapping[text]
        # Generate deterministic embedding from text hash
        seed = int.from_bytes(text.encode()[:4], "big")
        return _make_embedding(seed)

    async def embed_single(self, text: str) -> list[float]:
        return self._get_embedding(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._get_embedding(t) for t in texts]


# ---------------------------------------------------------------------------
# GOOD SANDWICHES (expected validity > 0.7)
# ---------------------------------------------------------------------------


class TestGoodSandwiches:
    """Three well-formed sandwiches that should score > 0.7."""

    @pytest.mark.asyncio
    async def test_squeeze_theorem(self):
        """The Squeeze Theorem: a canonical bound sandwich."""
        bread_top = "Upper bound function g(x) where g(x) >= f(x)"
        filling = "Target function f(x) whose limit we seek"
        bread_bottom = "Lower bound function h(x) where h(x) <= f(x)"

        # Bread embeddings should be similar to each other (related concepts)
        # but filling should be distinct from both breads
        emb_top = _make_embedding(100)
        emb_bottom = _make_similar_embedding(emb_top, noise=0.1)
        emb_filling = _make_embedding(200)  # Distinct from bread

        llm = MockLLM(bread_compat=0.9, containment=0.95, rationale="Perfect bound structure")
        embeds = MockEmbeddingService({
            bread_top: emb_top,
            bread_bottom: emb_bottom,
            filling: emb_filling,
        })

        result = await validate_sandwich(
            name="The Squeeze",
            bread_top=bread_top,
            bread_bottom=bread_bottom,
            filling=filling,
            structure_type="bound",
            description="When both bounds converge to L, the filling is squeezed to L",
            containment_argument="f(x) cannot escape the bounds; its limit is determined by theirs",
            llm=llm,
            embeddings=embeds,
        )

        _print_scores("Squeeze Theorem", result)
        assert result.overall_score > 0.7, f"Expected > 0.7, got {result.overall_score:.3f}"
        assert result.recommendation == "accept"

    @pytest.mark.asyncio
    async def test_bayesian_blt(self):
        """The Bayesian BLT: posterior between prior and likelihood."""
        bread_top = "Prior distribution P(theta) encoding beliefs before data"
        filling = "Posterior distribution P(theta|D) updated beliefs"
        bread_bottom = "Likelihood function P(D|theta) probability of data given parameter"

        emb_top = _make_embedding(300)
        emb_bottom = _make_similar_embedding(emb_top, noise=0.1)
        emb_filling = _make_embedding(400)

        llm = MockLLM(bread_compat=0.85, containment=0.9, rationale="Strong stochastic sandwich")
        embeds = MockEmbeddingService({
            bread_top: emb_top,
            bread_bottom: emb_bottom,
            filling: emb_filling,
        })

        result = await validate_sandwich(
            name="The Bayesian BLT",
            bread_top=bread_top,
            bread_bottom=bread_bottom,
            filling=filling,
            structure_type="stochastic",
            description="The posterior is proportional to prior times likelihood",
            containment_argument="The posterior has no independent existence without both prior and likelihood",
            llm=llm,
            embeddings=embeds,
        )

        _print_scores("Bayesian BLT", result)
        assert result.overall_score > 0.7, f"Expected > 0.7, got {result.overall_score:.3f}"
        assert result.recommendation == "accept"

    @pytest.mark.asyncio
    async def test_regulatory_reuben(self):
        """The Regulatory Reuben: practices between safety and budget."""
        bread_top = "Minimum safety standards required by law"
        filling = "Actual company safety practices"
        bread_bottom = "Maximum cost constraints from budget"

        emb_top = _make_embedding(500)
        emb_bottom = _make_similar_embedding(emb_top, noise=0.15)
        emb_filling = _make_embedding(600)

        llm = MockLLM(bread_compat=0.8, containment=0.85, rationale="Good optimization sandwich")
        embeds = MockEmbeddingService({
            bread_top: emb_top,
            bread_bottom: emb_bottom,
            filling: emb_filling,
        })

        result = await validate_sandwich(
            name="The Regulatory Reuben",
            bread_top=bread_top,
            bread_bottom=bread_bottom,
            filling=filling,
            structure_type="optimization",
            description="Company practices must satisfy regulations while staying under budget",
            containment_argument="Practices below minimum are illegal; above maximum are unaffordable",
            llm=llm,
            embeddings=embeds,
        )

        _print_scores("Regulatory Reuben", result)
        assert result.overall_score > 0.7, f"Expected > 0.7, got {result.overall_score:.3f}"
        assert result.recommendation == "accept"


# ---------------------------------------------------------------------------
# BAD SANDWICHES (expected validity < 0.5)
# ---------------------------------------------------------------------------


class TestBadSandwiches:
    """Three malformed sandwiches that should score < 0.5."""

    @pytest.mark.asyncio
    async def test_trivial_sandwich(self):
        """Filling is same as bread - should fail nontrivial check."""
        bread_top = "Dogs"
        filling = "Dogs"
        bread_bottom = "Canines"

        # Make filling identical to bread_top and very similar to bread_bottom
        emb_top = _make_embedding(700)
        emb_filling = _make_identical_embedding(emb_top)  # sim = 1.0
        emb_bottom = _make_similar_embedding(emb_top, noise=0.05)

        llm = MockLLM(
            bread_compat=0.4,
            containment=0.2,
            rationale="Filling is the same as bread; trivial",
        )
        embeds = MockEmbeddingService({
            bread_top: emb_top,
            bread_bottom: emb_bottom,
            filling: emb_filling,
        })

        result = await validate_sandwich(
            name="The Dog",
            bread_top=bread_top,
            bread_bottom=bread_bottom,
            filling=filling,
            structure_type="definitional",
            description="Dogs are dogs",
            containment_argument="Dogs are contained by dogs",
            llm=llm,
            embeddings=embeds,
        )

        _print_scores("Trivial (Dogs)", result)
        assert result.overall_score < 0.5, f"Expected < 0.5, got {result.overall_score:.3f}"
        assert result.recommendation == "reject"

    @pytest.mark.asyncio
    async def test_unrelated_bread(self):
        """Breads are completely unrelated - should fail bread_compat."""
        bread_top = "The color blue"
        filling = "Monetary policy decisions"
        bread_bottom = "Guitar string tension"

        emb_top = _make_embedding(800)
        emb_bottom = _make_embedding(900)
        emb_filling = _make_embedding(1000)

        llm = MockLLM(
            bread_compat=0.1,
            containment=0.15,
            rationale="Breads have no relationship; filling is unrelated to both",
        )
        embeds = MockEmbeddingService({
            bread_top: emb_top,
            bread_bottom: emb_bottom,
            filling: emb_filling,
        })

        result = await validate_sandwich(
            name="The Nonsense",
            bread_top=bread_top,
            bread_bottom=bread_bottom,
            filling=filling,
            structure_type="bound",
            description="Blue and guitar tension bound monetary policy",
            containment_argument="None",
            llm=llm,
            embeddings=embeds,
        )

        _print_scores("Unrelated Bread", result)
        assert result.overall_score < 0.5, f"Expected < 0.5, got {result.overall_score:.3f}"
        assert result.recommendation == "reject"

    @pytest.mark.asyncio
    async def test_no_containment(self):
        """Filling is not bounded by bread - should fail containment."""
        bread_top = "Breakfast time"
        filling = "The concept of justice"
        bread_bottom = "Dinner time"

        emb_top = _make_embedding(1100)
        emb_bottom = _make_similar_embedding(emb_top, noise=0.1)
        emb_filling = _make_embedding(1200)

        llm = MockLLM(
            bread_compat=0.25,
            containment=0.1,
            rationale="Bread is related (both are meal times) but filling has no containment relationship",
        )
        embeds = MockEmbeddingService({
            bread_top: emb_top,
            bread_bottom: emb_bottom,
            filling: emb_filling,
        })

        result = await validate_sandwich(
            name="The Justice Meal",
            bread_top=bread_top,
            bread_bottom=bread_bottom,
            filling=filling,
            structure_type="temporal",
            description="Justice sits between breakfast and dinner",
            containment_argument="Justice is not bounded by meal times",
            llm=llm,
            embeddings=embeds,
        )

        _print_scores("No Containment", result)
        assert result.overall_score < 0.5, f"Expected < 0.5, got {result.overall_score:.3f}"
        assert result.recommendation == "reject"


# ---------------------------------------------------------------------------
# Unit tests for internal functions
# ---------------------------------------------------------------------------


class TestCosineSimlarity:
    """Test the cosine similarity helper."""

    def test_identical_vectors(self):
        v = [1.0, 0.0, 0.0]
        assert _cosine_similarity(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        a = [1.0, 0.0, 0.0]
        b = [0.0, 1.0, 0.0]
        assert _cosine_similarity(a, b) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert _cosine_similarity(a, b) == pytest.approx(-1.0)

    def test_zero_vector(self):
        a = [0.0, 0.0]
        b = [1.0, 0.0]
        assert _cosine_similarity(a, b) == 0.0


class TestValidationConfig:
    """Test that config weights sum to 1.0."""

    def test_default_weights_sum(self):
        cfg = ValidationConfig()
        total = (
            cfg.weight_bread_compat
            + cfg.weight_containment
            + cfg.weight_nontrivial
            + cfg.weight_novelty
        )
        assert total == pytest.approx(1.0)


class TestNoveltyWithCorpus:
    """Test that novelty scoring works with corpus embeddings."""

    @pytest.mark.asyncio
    async def test_novelty_decreases_with_similar_corpus(self):
        """A sandwich similar to existing corpus should have lower novelty."""
        bread_top = "Concept A top"
        filling = "Concept A filling"
        bread_bottom = "Concept A bottom"

        emb_top = _make_embedding(1300)
        emb_bottom = _make_similar_embedding(emb_top, noise=0.1)
        emb_filling = _make_embedding(1400)

        # Create a corpus embedding that is the average (same as what validator computes)
        corpus_emb = [
            (a + b + c) / 3.0
            for a, b, c in zip(emb_top, emb_bottom, emb_filling)
        ]
        norm = math.sqrt(sum(x * x for x in corpus_emb))
        corpus_emb = [x / norm for x in corpus_emb]

        llm = MockLLM(bread_compat=0.8, containment=0.8, rationale="Good sandwich")
        embeds = MockEmbeddingService({
            bread_top: emb_top,
            bread_bottom: emb_bottom,
            filling: emb_filling,
        })

        # Without corpus
        result_no_corpus = await validate_sandwich(
            name="Test",
            bread_top=bread_top,
            bread_bottom=bread_bottom,
            filling=filling,
            structure_type="bound",
            description="test",
            containment_argument="test",
            llm=llm,
            embeddings=embeds,
            corpus_embeddings=None,
        )

        # With similar corpus
        result_with_corpus = await validate_sandwich(
            name="Test",
            bread_top=bread_top,
            bread_bottom=bread_bottom,
            filling=filling,
            structure_type="bound",
            description="test",
            containment_argument="test",
            llm=llm,
            embeddings=embeds,
            corpus_embeddings=[corpus_emb],
        )

        assert result_no_corpus.novelty_score == 1.0
        assert result_with_corpus.novelty_score < result_no_corpus.novelty_score


# ---------------------------------------------------------------------------
# Score printer
# ---------------------------------------------------------------------------


def _print_scores(name: str, result: ValidationResult) -> None:
    """Print detailed scores for a sandwich (visible during test runs with -s)."""
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    print(f"  bread_compat:  {result.bread_compat_score:.3f}  (weight 0.25)")
    print(f"  containment:   {result.containment_score:.3f}  (weight 0.35)")
    print(f"  nontrivial:    {result.nontrivial_score:.3f}  (weight 0.20)")
    print(f"  novelty:       {result.novelty_score:.3f}  (weight 0.20)")
    print(f"  -----------------------------------------")
    print(f"  OVERALL:       {result.overall_score:.3f}")
    print(f"  RECOMMENDATION: {result.recommendation}")
    print(f"  RATIONALE: {result.rationale}")
    print(f"{'='*60}")
