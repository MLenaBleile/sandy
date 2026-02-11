"""Tests for the full sandwich-making pipeline.

Reference: PROMPTS.md Prompt 7
"""

import json
import math
import random
import textwrap
from unittest.mock import AsyncMock

import pytest

from sandwich.agent.pipeline import (
    PipelineConfig,
    SourceMetadata,
    StoredSandwich,
    make_sandwich,
)
from sandwich.agent.preprocessor import PreprocessConfig
from sandwich.agent.selector import SelectionConfig
from sandwich.agent.validator import ValidationConfig
from sandwich.db.corpus import CorpusIngredient, SandwichCorpus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_embedding(seed: int, dim: int = 32) -> list[float]:
    """Generate a deterministic unit-length pseudo-random vector."""
    rng = random.Random(seed)
    raw = [rng.gauss(0, 1) for _ in range(dim)]
    norm = math.sqrt(sum(x * x for x in raw))
    return [x / norm for x in raw]


SQUEEZE_CONTENT = textwrap.dedent("""\
    The squeeze theorem, also known as the sandwich theorem, is a fundamental
    result in mathematical analysis. It provides a method for evaluating the
    limit of a function by bounding it between two other functions whose limits
    are already known.

    Formally, suppose that for all x in some interval containing c (except
    possibly at c itself), we have g(x) <= f(x) <= h(x). If both g(x) and h(x)
    approach the same limit L as x approaches c, then f(x) must also approach L.

    This theorem is particularly useful in situations where direct computation of
    a limit is difficult or impossible. For example, consider the well-known limit
    of sin(x)/x as x approaches 0. By establishing appropriate upper and lower
    bounds using geometric arguments on the unit circle, we can show that this
    limit equals 1.

    The applications of the squeeze theorem extend beyond elementary calculus.
    In real analysis, it plays a crucial role in proving the convergence of
    sequences and series. In probability theory, analogous bounding arguments
    appear in the proof of the law of large numbers.
""")

GOOD_IDENTIFIER_RESPONSE = {
    "candidates": [
        {
            "bread_top": "Upper bound function g(x) where g(x) >= f(x)",
            "bread_bottom": "Lower bound function h(x) where h(x) <= f(x)",
            "filling": "Target function f(x) whose limit we seek",
            "structure_type": "bound",
            "confidence": 0.95,
            "rationale": "The squeeze theorem is a perfect sandwich.",
        }
    ],
    "no_sandwich_reason": None,
}

GOOD_ASSEMBLER_RESPONSE = {
    "name": "The Squeeze",
    "description": (
        "The squeeze theorem sandwich—when f(x) is trapped between g(x) and h(x), "
        "and both bounds converge to L, the filling must also converge to L."
    ),
    "containment_argument": (
        "The target function f(x) is constrained above by g(x) and below by h(x). "
        "Without either bound, f(x) could wander freely."
    ),
    "sandy_commentary": "A perfect sandwich. The filling does not choose its fate. Nourishing.",
}

GOOD_VALIDATOR_RESPONSE = {
    "bread_compat_score": 0.90,
    "containment_score": 0.95,
    "specificity_score": 0.85,
    "rationale": "Perfect bound structure with clear containment.",
}

REJECT_VALIDATOR_RESPONSE = {
    "bread_compat_score": 0.20,
    "containment_score": 0.15,
    "specificity_score": 0.30,
    "rationale": "The bread elements are unrelated and containment is absent.",
}

GIBBERISH_IDENTIFIER_RESPONSE = {
    "candidates": [],
    "no_sandwich_reason": "All filling, no structure. A soup of nonsense.",
}

TRIVIAL_IDENTIFIER_RESPONSE = {
    "candidates": [
        {
            "bread_top": "Dogs",
            "bread_bottom": "Canines",
            "filling": "Dogs",
            "structure_type": "definitional",
            "confidence": 0.8,
            "rationale": "Dogs are dogs.",
        }
    ],
    "no_sandwich_reason": None,
}

TRIVIAL_ASSEMBLER_RESPONSE = {
    "name": "The Dog",
    "description": "Dogs between dogs. Not a sandwich.",
    "containment_argument": "The filling is the bread. There is no containment.",
    "sandy_commentary": "This is not a sandwich. This is self-reference.",
}


def _make_mock_llm(
    identifier_response: dict,
    assembler_response: dict,
    validator_response: dict,
) -> AsyncMock:
    """Create a mock LLM for pipeline testing."""
    llm = AsyncMock()
    llm.identify_ingredients = AsyncMock(
        return_value=json.dumps(identifier_response)
    )
    llm.assemble_sandwich = AsyncMock(
        return_value=json.dumps(assembler_response)
    )
    llm.raw_call = AsyncMock(
        return_value=json.dumps(validator_response)
    )
    return llm


def _make_mock_embeddings(dim: int = 32) -> AsyncMock:
    """Create a mock embedding service that returns distinct vectors."""
    call_count = [0]

    async def _embed_single(text: str) -> list[float]:
        call_count[0] += 1
        return _make_embedding(seed=hash(text) % 10000, dim=dim)

    async def _embed_batch(texts: list[str]) -> list[list[float]]:
        results = []
        for t in texts:
            call_count[0] += 1
            results.append(_make_embedding(seed=hash(t) % 10000, dim=dim))
        return results

    emb = AsyncMock()
    emb.embed_single = AsyncMock(side_effect=_embed_single)
    emb.embed_batch = AsyncMock(side_effect=_embed_batch)
    return emb


# ===================================================================
# test_full_pipeline_success
# ===================================================================

class TestFullPipelineSuccess:
    """Verify end-to-end pipeline produces a StoredSandwich."""

    @pytest.mark.asyncio
    async def test_full_pipeline_success(self):
        llm = _make_mock_llm(
            GOOD_IDENTIFIER_RESPONSE,
            GOOD_ASSEMBLER_RESPONSE,
            GOOD_VALIDATOR_RESPONSE,
        )
        embeddings = _make_mock_embeddings()
        corpus = SandwichCorpus()
        source = SourceMetadata(url="https://en.wikipedia.org/wiki/Squeeze_theorem")

        result, outcome = await make_sandwich(
            SQUEEZE_CONTENT, source, corpus, llm, embeddings
        )

        assert result is not None, f"Pipeline failed: {outcome.detail}"
        assert isinstance(result, StoredSandwich)
        assert result.assembled.name == "The Squeeze"
        assert result.validation.recommendation in ("accept", "review")
        assert result.embeddings.bread_top is not None
        assert result.embeddings.bread_bottom is not None
        assert result.embeddings.filling is not None
        assert result.embeddings.full is not None
        assert outcome.stage == "storage"
        assert outcome.outcome == "success"

        # Verify corpus was updated
        assert corpus.total_sandwiches == 1
        assert len(corpus.ingredients) == 3

        # Verify ingredients were created
        assert "bread_top" in result.ingredients
        assert "bread_bottom" in result.ingredients
        assert "filling" in result.ingredients


# ===================================================================
# test_pipeline_preprocessor_rejection
# ===================================================================

class TestPipelinePreprocessorRejection:
    """Verify short content is rejected at preprocessing."""

    @pytest.mark.asyncio
    async def test_pipeline_preprocessor_rejection(self):
        llm = _make_mock_llm(
            GOOD_IDENTIFIER_RESPONSE,
            GOOD_ASSEMBLER_RESPONSE,
            GOOD_VALIDATOR_RESPONSE,
        )
        embeddings = _make_mock_embeddings()
        corpus = SandwichCorpus()
        source = SourceMetadata()

        result, outcome = await make_sandwich(
            "Too short.", source, corpus, llm, embeddings
        )

        assert result is None
        assert outcome.stage == "preprocessing"
        assert outcome.outcome == "skipped"
        assert "too_short" in outcome.detail

        # LLM should not have been called
        llm.identify_ingredients.assert_not_awaited()


# ===================================================================
# test_pipeline_no_candidates
# ===================================================================

class TestPipelineNoCandidates:
    """Verify gibberish content produces no candidates."""

    @pytest.mark.asyncio
    async def test_pipeline_no_candidates(self):
        # Need content long enough to pass preprocessing
        gibberish = textwrap.dedent("""\
            The analysis of various methodological approaches to understanding
            the relationship between different theoretical frameworks reveals
            several important considerations. First, the epistemological
            foundations must be carefully examined. Second, the ontological
            commitments implicit in each framework deserve scrutiny. Third,
            the pragmatic implications of adopting one approach over another
            should be weighed carefully.

            Furthermore, the hermeneutic tradition offers additional insights
            into how interpretive practices shape our understanding of these
            complex phenomena. The dialectical interplay between theory and
            practice remains a central concern for researchers across multiple
            disciplines.
        """)

        llm = _make_mock_llm(
            GIBBERISH_IDENTIFIER_RESPONSE,
            GOOD_ASSEMBLER_RESPONSE,
            GOOD_VALIDATOR_RESPONSE,
        )
        embeddings = _make_mock_embeddings()
        corpus = SandwichCorpus()
        source = SourceMetadata()

        result, outcome = await make_sandwich(
            gibberish, source, corpus, llm, embeddings
        )

        assert result is None
        assert outcome.stage == "identification"
        assert outcome.outcome == "no_candidates"


# ===================================================================
# test_pipeline_validation_rejection
# ===================================================================

class TestPipelineValidationRejection:
    """Verify a trivial sandwich is rejected at validation."""

    @pytest.mark.asyncio
    async def test_pipeline_validation_rejection(self):
        trivial_content = textwrap.dedent("""\
            Dogs are domesticated mammals, not natural wild animals. They were
            originally bred from wolves. They have been bred by humans for a
            long time, and were the first animals ever to be domesticated.
            Dogs are sometimes referred to as canines from the Latin word for
            dog, canis. There are many different breeds of dogs.

            The domestic dog is a member of the genus Canis, which forms part
            of the wolf-like canids. The dog is the most widely abundant
            terrestrial carnivore. Dogs and wolves are closely related through
            a close genetic relationship.
        """)

        llm = _make_mock_llm(
            TRIVIAL_IDENTIFIER_RESPONSE,
            TRIVIAL_ASSEMBLER_RESPONSE,
            REJECT_VALIDATOR_RESPONSE,
        )
        embeddings = _make_mock_embeddings()
        corpus = SandwichCorpus()
        source = SourceMetadata()

        result, outcome = await make_sandwich(
            trivial_content, source, corpus, llm, embeddings
        )

        assert result is None
        assert outcome.stage == "validation"
        assert outcome.outcome == "rejected"


# ===================================================================
# test_ingredient_reuse
# ===================================================================

class TestIngredientReuse:
    """Verify ingredients are reused across sandwiches."""

    @pytest.mark.asyncio
    async def test_ingredient_reuse(self):
        # First sandwich
        llm = _make_mock_llm(
            GOOD_IDENTIFIER_RESPONSE,
            GOOD_ASSEMBLER_RESPONSE,
            GOOD_VALIDATOR_RESPONSE,
        )
        embeddings = _make_mock_embeddings()
        corpus = SandwichCorpus()
        source = SourceMetadata()

        result1, outcome1 = await make_sandwich(
            SQUEEZE_CONTENT, source, corpus, llm, embeddings
        )
        assert result1 is not None

        # Second sandwich with same bread top text
        # (LLM returns same identifier results, so bread_top is identical)
        result2, outcome2 = await make_sandwich(
            SQUEEZE_CONTENT, source, corpus, llm, embeddings
        )
        assert result2 is not None

        # The bread_top ingredient should have been reused
        bread_top_ing = result2.ingredients["bread_top"]
        assert bread_top_ing.usage_count == 2, (
            f"Expected usage_count=2, got {bread_top_ing.usage_count}"
        )

        # Corpus should have 2 sandwiches but 3 unique ingredients
        # (all three are reused, so still 3)
        assert corpus.total_sandwiches == 2
        assert len(corpus.ingredients) == 3  # no new ingredients on second run


# ===================================================================
# test_corpus_updated_on_success
# ===================================================================

class TestCorpusUpdatedOnSuccess:
    """Verify the corpus is updated with embeddings and type counts."""

    @pytest.mark.asyncio
    async def test_corpus_updated(self):
        llm = _make_mock_llm(
            GOOD_IDENTIFIER_RESPONSE,
            GOOD_ASSEMBLER_RESPONSE,
            GOOD_VALIDATOR_RESPONSE,
        )
        embeddings = _make_mock_embeddings()
        corpus = SandwichCorpus()
        source = SourceMetadata()

        assert corpus.is_empty()

        result, _ = await make_sandwich(
            SQUEEZE_CONTENT, source, corpus, llm, embeddings
        )
        assert result is not None

        assert not corpus.is_empty()
        assert corpus.total_sandwiches == 1
        assert len(corpus.get_all_embeddings()) == 1
        assert "bound" in corpus.get_type_frequencies()
        assert corpus.get_type_frequencies()["bound"] == 1.0


# ===================================================================
# test_embeddings_batch_call
# ===================================================================

class TestEmbeddingsBatchCall:
    """Verify embeddings are generated via batch API call."""

    @pytest.mark.asyncio
    async def test_embeddings_batch_call(self):
        llm = _make_mock_llm(
            GOOD_IDENTIFIER_RESPONSE,
            GOOD_ASSEMBLER_RESPONSE,
            GOOD_VALIDATOR_RESPONSE,
        )
        embeddings = _make_mock_embeddings()
        corpus = SandwichCorpus()
        source = SourceMetadata()

        result, _ = await make_sandwich(
            SQUEEZE_CONTENT, source, corpus, llm, embeddings
        )
        assert result is not None

        # embed_batch should have been called (for validator + for sandwich embeddings)
        assert embeddings.embed_batch.await_count >= 1
