"""Sandwich validator - the critical quality gate.

Implements hybrid validation combining LLM-judged and embedding-based
scoring to determine whether an assembled sandwich is valid.

Reference: SPEC.md Sections 3.2.6, 14.5, 15
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional

from sandwich.errors.exceptions import ParseError
from sandwich.llm.interface import EmbeddingService, SandwichLLM
from sandwich.llm.retry import parse_with_recovery

logger = logging.getLogger(__name__)

# Resolve the path to the validator prompt template
_PROMPT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "prompts")
_VALIDATOR_PROMPT_PATH = os.path.join(_PROMPT_DIR, "validator.txt")


@dataclass
class ValidationConfig:
    """Weights and thresholds for sandwich validation."""

    weight_bread_compat: float = 0.20
    weight_containment: float = 0.25
    weight_specificity: float = 0.20
    weight_nontrivial: float = 0.15
    weight_novelty: float = 0.20

    accept_threshold: float = 0.7
    marginal_threshold: float = 0.5


@dataclass
class ValidationResult:
    """Complete validation result for a sandwich."""

    bread_compat_score: float
    containment_score: float
    specificity_score: float
    nontrivial_score: float
    novelty_score: float
    overall_score: float
    recommendation: str  # 'accept', 'review', 'reject'
    rationale: str


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _load_validator_prompt() -> str:
    """Load the validator prompt template from disk."""
    with open(_VALIDATOR_PROMPT_PATH, "r") as f:
        return f.read()


async def validate_sandwich(
    *,
    name: str,
    bread_top: str,
    bread_bottom: str,
    filling: str,
    structure_type: str,
    description: str,
    containment_argument: str,
    llm: SandwichLLM,
    embeddings: EmbeddingService,
    corpus_embeddings: Optional[list[list[float]]] = None,
    config: Optional[ValidationConfig] = None,
) -> ValidationResult:
    """Validate a sandwich using hybrid LLM + embedding scoring.

    Combines:
      a) LLM-judged: bread_compatibility and containment scores
      b) Embedding-based: nontrivial_score and novelty_score

    Args:
        name: Sandwich name.
        bread_top: Top bread concept.
        bread_bottom: Bottom bread concept.
        filling: Filling concept.
        structure_type: Structural type name.
        description: Sandwich description.
        containment_argument: Why filling is contained by bread.
        llm: LLM service for judging bread_compat and containment.
        embeddings: Embedding service for computing similarity.
        corpus_embeddings: Existing sandwich embeddings for novelty check.
            If None or empty, novelty defaults to 1.0.
        config: Validation configuration.

    Returns:
        ValidationResult with all component scores and recommendation.
    """
    cfg = config or ValidationConfig()

    # --- (a) LLM-judged scores: bread_compat and containment ---
    prompt_template = _load_validator_prompt()
    prompt = prompt_template.format(
        name=name,
        bread_top=bread_top,
        bread_bottom=bread_bottom,
        filling=filling,
        structure_type=structure_type,
        description=description,
        containment_argument=containment_argument,
    )

    raw_response = await llm.raw_call(
        system_prompt="You are a rigorous evaluator of knowledge sandwiches.",
        user_prompt=prompt,
    )

    async def _retry_call(retry_prompt: str) -> str:
        return await llm.raw_call(
            system_prompt="You are a rigorous evaluator of knowledge sandwiches.",
            user_prompt=retry_prompt,
        )

    retry_prompt = (
        "Your previous response could not be parsed. "
        "Please respond ONLY with a valid JSON object with exactly these keys: "
        "bread_compat_score (float 0-1), containment_score (float 0-1), "
        "specificity_score (float 0-1), rationale (string). No other text."
    )

    parsed = await parse_with_recovery(
        raw_response,
        required_fields=["bread_compat_score", "containment_score", "specificity_score", "rationale"],
        llm_call=_retry_call,
        retry_prompt=retry_prompt,
    )

    bread_compat_score = float(parsed["bread_compat_score"])
    containment_score = float(parsed["containment_score"])
    specificity_score = float(parsed["specificity_score"])
    llm_rationale = parsed["rationale"]

    # Clamp to [0, 1]
    bread_compat_score = max(0.0, min(1.0, bread_compat_score))
    containment_score = max(0.0, min(1.0, containment_score))
    specificity_score = max(0.0, min(1.0, specificity_score))

    # --- (b) Embedding-based scores ---

    # Get embeddings for bread and filling
    emb_results = await embeddings.embed_batch([bread_top, bread_bottom, filling])
    emb_bread_top = emb_results[0]
    emb_bread_bottom = emb_results[1]
    emb_filling = emb_results[2]

    # nontrivial_score: 1 - max(sim(filling, bread_top), sim(filling, bread_bottom))
    sim_top = _cosine_similarity(emb_filling, emb_bread_top)
    sim_bottom = _cosine_similarity(emb_filling, emb_bread_bottom)
    nontrivial_score = 1.0 - max(sim_top, sim_bottom)
    nontrivial_score = max(0.0, min(1.0, nontrivial_score))

    # novelty_score: 1 - max_similarity_to_corpus (or 1.0 if corpus empty)
    if corpus_embeddings:
        # Compute full sandwich embedding as average of components
        full_emb = [
            (a + b + c) / 3.0
            for a, b, c in zip(emb_bread_top, emb_bread_bottom, emb_filling)
        ]
        max_sim = max(
            _cosine_similarity(full_emb, corpus_emb)
            for corpus_emb in corpus_embeddings
        )
        novelty_score = 1.0 - max_sim
        novelty_score = max(0.0, min(1.0, novelty_score))
    else:
        novelty_score = 1.0

    # --- (c) Combine into overall score ---
    overall = (
        cfg.weight_bread_compat * bread_compat_score
        + cfg.weight_containment * containment_score
        + cfg.weight_specificity * specificity_score
        + cfg.weight_nontrivial * nontrivial_score
        + cfg.weight_novelty * novelty_score
    )

    # Determine recommendation
    if overall >= cfg.accept_threshold:
        recommendation = "accept"
    elif overall >= cfg.marginal_threshold:
        recommendation = "review"
    else:
        recommendation = "reject"

    rationale = (
        f"LLM: {llm_rationale} | "
        f"Specificity: {specificity_score:.3f} | "
        f"Nontrivial: sim(filling,top)={sim_top:.3f}, sim(filling,bottom)={sim_bottom:.3f} | "
        f"Novelty: {'corpus empty' if not corpus_embeddings else f'max_corpus_sim={1.0 - novelty_score:.3f}'}"
    )

    logger.info(
        "Validation: bread_compat=%.3f containment=%.3f specificity=%.3f nontrivial=%.3f novelty=%.3f "
        "overall=%.3f recommendation=%s",
        bread_compat_score,
        containment_score,
        specificity_score,
        nontrivial_score,
        novelty_score,
        overall,
        recommendation,
    )

    return ValidationResult(
        bread_compat_score=bread_compat_score,
        containment_score=containment_score,
        specificity_score=specificity_score,
        nontrivial_score=nontrivial_score,
        novelty_score=novelty_score,
        overall_score=overall,
        recommendation=recommendation,
        rationale=rationale,
    )
