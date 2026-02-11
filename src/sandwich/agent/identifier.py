"""Ingredient identifier – extracts candidate sandwich structures from content.

Reference: SPEC.md Sections 3.2.3, 3.2.4, 14.3; PROMPTS.md Prompt 5
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

from sandwich.llm.interface import SandwichLLM
from sandwich.llm.retry import parse_with_recovery

logger = logging.getLogger(__name__)

_PROMPT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "prompts")
_IDENTIFIER_PROMPT_PATH = os.path.join(_PROMPT_DIR, "identifier.txt")

VALID_STRUCTURE_TYPES = frozenset({
    "bound",
    "dialectic",
    "epistemic",
    "temporal",
    "perspectival",
    "conditional",
    "stochastic",
    "optimization",
    "negotiation",
    "definitional",
})


@dataclass
class CandidateStructure:
    """A single candidate sandwich structure extracted from content."""

    bread_top: str
    bread_bottom: str
    filling: str
    structure_type: str
    confidence: float
    rationale: str


@dataclass
class IdentificationResult:
    """Result of the identification stage."""

    candidates: list[CandidateStructure] = field(default_factory=list)
    no_sandwich_reason: Optional[str] = None


def _load_identifier_prompt() -> str:
    """Load the identifier prompt template from disk."""
    with open(_IDENTIFIER_PROMPT_PATH, "r") as f:
        return f.read()


def _parse_candidate(raw: dict) -> Optional[CandidateStructure]:
    """Parse a single candidate dict into a CandidateStructure.

    Returns None if the candidate is invalid (missing fields, bad types).
    """
    try:
        bread_top = str(raw["bread_top"]).strip()
        bread_bottom = str(raw["bread_bottom"]).strip()
        filling = str(raw["filling"]).strip()
        structure_type = str(raw.get("structure_type", "")).strip().lower()
        confidence = float(raw.get("confidence", 0.0))
        rationale = str(raw.get("rationale", "")).strip()
    except (KeyError, TypeError, ValueError) as exc:
        logger.debug("Skipping malformed candidate: %s", exc)
        return None

    if not bread_top or not bread_bottom or not filling:
        return None

    # Clamp confidence to [0, 1]
    confidence = max(0.0, min(1.0, confidence))

    # Normalise structure_type to closest valid type, or keep as-is
    if structure_type not in VALID_STRUCTURE_TYPES:
        logger.debug(
            "Unknown structure_type '%s', keeping as-is", structure_type
        )

    return CandidateStructure(
        bread_top=bread_top,
        bread_bottom=bread_bottom,
        filling=filling,
        structure_type=structure_type,
        confidence=confidence,
        rationale=rationale,
    )


async def identify_ingredients(
    content: str,
    llm: SandwichLLM,
) -> IdentificationResult:
    """Identify candidate sandwich structures from content.

    Args:
        content: Preprocessed source content.
        llm: LLM service for ingredient identification.

    Returns:
        IdentificationResult with candidates sorted by confidence (descending).
    """
    prompt_template = _load_identifier_prompt()
    prompt = prompt_template.format(content=content)

    raw_response = await llm.identify_ingredients(content)

    # Recovery prompt for parse failures
    retry_prompt = (
        "Your previous response could not be parsed. "
        "Please respond ONLY with a valid JSON object with exactly these keys: "
        '"candidates" (list of objects with bread_top, bread_bottom, filling, '
        'structure_type, confidence, rationale), "no_sandwich_reason" (string or null). '
        "No other text."
    )

    async def _retry_call(rp: str) -> str:
        return await llm.raw_call(
            system_prompt="You are Sandy, examining content for sandwich potential.",
            user_prompt=rp,
        )

    try:
        parsed = await parse_with_recovery(
            raw_response,
            required_fields=["candidates"],
            llm_call=_retry_call,
            retry_prompt=retry_prompt,
        )
    except Exception:
        logger.warning("Failed to parse identifier response, returning no candidates")
        return IdentificationResult(
            candidates=[],
            no_sandwich_reason="Could not parse identification results.",
        )

    # Parse candidates
    raw_candidates = parsed.get("candidates", [])
    if not isinstance(raw_candidates, list):
        raw_candidates = []

    candidates: list[CandidateStructure] = []
    for raw_cand in raw_candidates:
        cand = _parse_candidate(raw_cand)
        if cand is not None:
            candidates.append(cand)

    # Sort by confidence descending
    candidates.sort(key=lambda c: c.confidence, reverse=True)

    # Cap at 3 candidates as specified
    candidates = candidates[:3]

    no_reason = parsed.get("no_sandwich_reason")
    if no_reason and not candidates:
        no_sandwich_reason = str(no_reason)
    elif not candidates:
        no_sandwich_reason = "No viable sandwich structures identified."
    else:
        no_sandwich_reason = None

    logger.info(
        "Identified %d candidate(s) from content (%d chars)",
        len(candidates),
        len(content),
    )

    return IdentificationResult(
        candidates=candidates,
        no_sandwich_reason=no_sandwich_reason,
    )
