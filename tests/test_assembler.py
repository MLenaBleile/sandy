"""Tests for the sandwich assembler module.

Reference: PROMPTS.md Prompt 6
"""

import json
import textwrap
from unittest.mock import AsyncMock

import pytest

from sandwich.agent.assembler import AssembledSandwich, assemble_sandwich
from sandwich.agent.identifier import CandidateStructure


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SQUEEZE_CANDIDATE = CandidateStructure(
    bread_top="Upper bound function g(x) where g(x) >= f(x)",
    bread_bottom="Lower bound function h(x) where h(x) <= f(x)",
    filling="Target function f(x) whose limit we seek",
    structure_type="bound",
    confidence=0.95,
    rationale="The squeeze theorem is a perfect sandwich.",
)

BAYESIAN_CANDIDATE = CandidateStructure(
    bread_top="Prior distribution P(θ) encoding beliefs before data",
    bread_bottom="Likelihood function P(D|θ) probability of data given parameter",
    filling="Posterior distribution P(θ|D) updated beliefs",
    structure_type="stochastic",
    confidence=0.90,
    rationale="Bayesian inference constrains the posterior between prior and likelihood.",
)

DIPLOMATIC_CANDIDATE = CandidateStructure(
    bread_top="Country A's opening position: full tariff protection",
    bread_bottom="Country B's opening position: zero tariffs",
    filling="Final agreement: partial tariffs with phase-out schedule",
    structure_type="negotiation",
    confidence=0.85,
    rationale="The compromise is bounded by the two negotiating positions.",
)

SQUEEZE_CONTENT = textwrap.dedent("""\
    The squeeze theorem, also known as the sandwich theorem, is a fundamental
    result in mathematical analysis. It provides a method for evaluating the
    limit of a function by bounding it between two other functions whose limits
    are already known.

    Formally, suppose that for all x in some interval containing c, we have
    g(x) <= f(x) <= h(x). If both g(x) and h(x) approach the same limit L
    as x approaches c, then f(x) must also approach L.
""")

BAYESIAN_CONTENT = textwrap.dedent("""\
    Bayesian inference is a method of statistical inference in which Bayes'
    theorem is used to update the probability for a hypothesis as more evidence
    or information becomes available. The prior distribution captures initial
    beliefs, the likelihood captures the data, and the posterior distribution
    represents updated beliefs after observing data.
""")

DIPLOMATIC_CONTENT = textwrap.dedent("""\
    International trade negotiations between Country A and Country B reached a
    conclusion after months of deliberation. Country A initially demanded full
    tariff protection for its domestic industries, while Country B pushed for
    complete elimination of trade barriers. The final agreement established
    a partial tariff regime with a ten-year phase-out schedule.
""")

# Mock LLM responses for each candidate
SQUEEZE_RESPONSE = {
    "name": "The Squeeze",
    "description": (
        "The squeeze theorem sandwich—when f(x) is trapped between g(x) and h(x), "
        "and both bounds converge to L, the filling must also converge to L. "
        "The bread compresses; the filling has no escape."
    ),
    "containment_argument": (
        "The target function f(x) has no independent fate. It is constrained above "
        "by g(x) and below by h(x). Without either bound, f(x) could wander freely. "
        "The bread determines the filling's destiny."
    ),
    "sandy_commentary": (
        "A perfect sandwich. The filling does not choose its fate. It is determined "
        "by the bread. This is the purest form. Nourishing."
    ),
}

BAYESIAN_RESPONSE = {
    "name": "The Bayesian BLT",
    "description": (
        "The posterior distribution is what emerges when prior beliefs meet observed "
        "data through the likelihood function. It cannot exist independently—it is "
        "proportional to the product of its bread."
    ),
    "containment_argument": (
        "The posterior P(θ|D) has no independent existence without both the prior "
        "P(θ) and the likelihood P(D|θ). Remove either bread and the filling "
        "collapses into meaninglessness."
    ),
    "sandy_commentary": (
        "The prior is yesterday's bread. The likelihood is today's. The posterior is "
        "what we eat now. Always fresh, always constrained by what came before. Satisfying."
    ),
}

DIPLOMATIC_RESPONSE = {
    "name": "The Diplomatic Dagwood",
    "description": (
        "Neither side got what they wanted. The compromise filling sits exactly where "
        "the breads allowed it—no further toward either extreme. A sandwich built by "
        "two bakers who could not agree on the recipe."
    ),
    "containment_argument": (
        "The partial tariff agreement cannot exceed Country A's demand for full "
        "protection, nor drop below Country B's push for zero tariffs. The bread "
        "defines the space of possible compromise."
    ),
    "sandy_commentary": (
        "Diplomacy is sandwich-making. Each party brings bread. The filling is what "
        "they can both swallow. Not elegant, but nourishing."
    ),
}


def _make_assembler_llm(response_json: dict) -> AsyncMock:
    """Create a mock SandwichLLM that returns the given assembly response."""
    llm = AsyncMock()
    llm.assemble_sandwich = AsyncMock(return_value=json.dumps(response_json))
    llm.raw_call = AsyncMock(return_value=json.dumps(response_json))
    return llm


# ===================================================================
# test_assembler_returns_valid_json
# ===================================================================

class TestAssemblerReturnsValidJson:
    """Verify assembler returns an AssembledSandwich with all fields populated."""

    @pytest.mark.asyncio
    async def test_assembler_returns_valid_json(self):
        llm = _make_assembler_llm(SQUEEZE_RESPONSE)

        result = await assemble_sandwich(SQUEEZE_CANDIDATE, SQUEEZE_CONTENT, llm)

        assert isinstance(result, AssembledSandwich)
        assert result.name == "The Squeeze"
        assert len(result.description) > 0
        assert len(result.containment_argument) > 0
        assert len(result.sandy_commentary) > 0
        assert result.bread_top == SQUEEZE_CANDIDATE.bread_top
        assert result.bread_bottom == SQUEEZE_CANDIDATE.bread_bottom
        assert result.filling == SQUEEZE_CANDIDATE.filling
        assert result.structure_type == "bound"
        assert len(result.source_content_snippet) > 0
        assert len(result.source_content_snippet) <= 500


# ===================================================================
# test_name_is_creative
# ===================================================================

class TestNameIsCreative:
    """Verify sandwich names are creative, diverse, and not generic."""

    @pytest.mark.asyncio
    async def test_name_is_creative(self):
        candidates_and_responses = [
            (SQUEEZE_CANDIDATE, SQUEEZE_CONTENT, SQUEEZE_RESPONSE),
            (BAYESIAN_CANDIDATE, BAYESIAN_CONTENT, BAYESIAN_RESPONSE),
            (DIPLOMATIC_CANDIDATE, DIPLOMATIC_CONTENT, DIPLOMATIC_RESPONSE),
        ]

        names = []
        for candidate, content, response in candidates_and_responses:
            llm = _make_assembler_llm(response)
            result = await assemble_sandwich(candidate, content, llm)
            names.append(result.name)

        # All names should be different
        assert len(set(names)) == 3, f"Names should be unique, got: {names}"

        # No generic names
        generic_names = {"Sandwich 1", "Sandwich 2", "Sandwich 3", "Untitled", "Sandwich", ""}
        for name in names:
            assert name not in generic_names, f"Name '{name}' is too generic"

        # Names should be non-trivially long (at least a few chars)
        for name in names:
            assert len(name) >= 3, f"Name '{name}' is too short"


# ===================================================================
# test_sandy_voice
# ===================================================================

class TestReubenVoice:
    """Verify commentary sounds like Reuben—no complaints, contemplative tone."""

    @pytest.mark.asyncio
    async def test_sandy_voice(self):
        llm = _make_assembler_llm(SQUEEZE_RESPONSE)
        result = await assemble_sandwich(SQUEEZE_CANDIDATE, SQUEEZE_CONTENT, llm)

        commentary = result.sandy_commentary.lower()

        # Should NOT contain complaint phrases
        complaint_phrases = ["i wish", "unfortunately", "i can't", "i cannot", "frustrating"]
        for phrase in complaint_phrases:
            assert phrase not in commentary, (
                f"Commentary should not contain '{phrase}': {result.sandy_commentary}"
            )

        # Should have contemplative/content tone — at least one positive indicator
        positive_indicators = [
            "nourishing", "satisfying", "perfect", "bread", "filling",
            "sandwich", "constrained", "determined", "elegant",
        ]
        found = [p for p in positive_indicators if p in commentary]
        assert len(found) > 0, (
            f"Commentary should have positive/contemplative tone. "
            f"None of {positive_indicators} found in: {result.sandy_commentary}"
        )


# ===================================================================
# test_containment_argument_present
# ===================================================================

class TestContainmentArgumentPresent:
    """Verify containment argument is substantive and references bread."""

    @pytest.mark.asyncio
    async def test_containment_argument_present(self):
        llm = _make_assembler_llm(SQUEEZE_RESPONSE)
        result = await assemble_sandwich(SQUEEZE_CANDIDATE, SQUEEZE_CONTENT, llm)

        # Should be substantive (> 50 chars)
        assert len(result.containment_argument) > 50, (
            f"Containment argument too short ({len(result.containment_argument)} chars): "
            f"{result.containment_argument}"
        )

        # Should reference bread concepts in some way
        arg_lower = result.containment_argument.lower()
        # Check for either the specific bread elements or generic bread references
        has_reference = (
            "bound" in arg_lower
            or "g(x)" in arg_lower
            or "h(x)" in arg_lower
            or "f(x)" in arg_lower
            or "bread" in arg_lower
            or "upper" in arg_lower
            or "lower" in arg_lower
        )
        assert has_reference, (
            f"Containment argument should reference bread elements: "
            f"{result.containment_argument}"
        )


# ===================================================================
# test_full_assembly
# ===================================================================

class TestFullAssembly:
    """End-to-end assembly of the squeeze theorem sandwich."""

    @pytest.mark.asyncio
    async def test_full_assembly(self):
        llm = _make_assembler_llm(SQUEEZE_RESPONSE)
        result = await assemble_sandwich(SQUEEZE_CANDIDATE, SQUEEZE_CONTENT, llm)

        # All fields populated and non-empty
        assert result.name
        assert result.description
        assert result.containment_argument
        assert result.sandy_commentary
        assert result.bread_top
        assert result.bread_bottom
        assert result.filling
        assert result.structure_type
        assert result.source_content_snippet

        # Structural integrity: type matches candidate
        assert result.structure_type == SQUEEZE_CANDIDATE.structure_type

        # Ingredients pass through from candidate
        assert result.bread_top == SQUEEZE_CANDIDATE.bread_top
        assert result.bread_bottom == SQUEEZE_CANDIDATE.bread_bottom
        assert result.filling == SQUEEZE_CANDIDATE.filling

        # Source snippet is bounded
        assert len(result.source_content_snippet) <= 500


# ===================================================================
# test_source_snippet_truncation
# ===================================================================

class TestSourceSnippetTruncation:
    """Verify source content is truncated to 500 chars."""

    @pytest.mark.asyncio
    async def test_long_content_truncated(self):
        long_content = "A" * 10000
        llm = _make_assembler_llm(SQUEEZE_RESPONSE)
        result = await assemble_sandwich(SQUEEZE_CANDIDATE, long_content, llm)

        assert len(result.source_content_snippet) == 500
