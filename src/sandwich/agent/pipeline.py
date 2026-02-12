"""Full sandwich-making pipeline.

Wires together: preprocess → identify → select → assemble → validate → store.

Reference: SPEC.md Sections 7.3, 9.2; PROMPTS.md Prompt 7
"""

import logging
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID, uuid4

from sandwich.agent.assembler import AssembledSandwich, assemble_sandwich
from sandwich.agent.identifier import identify_ingredients
from sandwich.agent.preprocessor import PreprocessConfig, preprocess
from sandwich.agent.selector import SelectionConfig, select_candidate
from sandwich.agent.validator import ValidationConfig, ValidationResult, validate_sandwich
from sandwich.db.corpus import CorpusIngredient, SandwichCorpus
from sandwich.llm.interface import EmbeddingService, SandwichLLM

logger = logging.getLogger(__name__)


@dataclass
class SourceMetadata:
    """Metadata about the content source."""

    url: Optional[str] = None
    domain: Optional[str] = None
    content_type: str = "text"  # 'html' or 'text'
    source_id: Optional[UUID] = None


@dataclass
class SandwichEmbeddings:
    """Embeddings for all parts of a sandwich."""

    bread_top: list[float]
    bread_bottom: list[float]
    filling: list[float]
    full: list[float]


@dataclass
class StoredSandwich:
    """A sandwich that has been validated and stored."""

    sandwich_id: UUID
    assembled: AssembledSandwich
    validation: ValidationResult
    embeddings: SandwichEmbeddings
    source_metadata: SourceMetadata
    ingredients: dict[str, CorpusIngredient] = field(default_factory=dict)


@dataclass
class PipelineConfig:
    """Configuration for the full pipeline."""

    preprocess: PreprocessConfig = field(default_factory=PreprocessConfig)
    selection: SelectionConfig = field(default_factory=SelectionConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)


@dataclass
class PipelineOutcome:
    """Record of a pipeline stage outcome for logging."""

    stage: str
    outcome: str
    detail: str


def _log_pipeline_outcome(stage: str, outcome: str, detail: str) -> PipelineOutcome:
    """Log and return a pipeline stage outcome."""
    logger.info("Pipeline [%s]: %s — %s", stage, outcome, detail)
    return PipelineOutcome(stage=stage, outcome=outcome, detail=detail)


async def generate_sandwich_embeddings(
    assembled: AssembledSandwich,
    embeddings: EmbeddingService,
) -> SandwichEmbeddings:
    """Generate embeddings for all sandwich components in a single batch call.

    Args:
        assembled: The assembled sandwich.
        embeddings: Embedding service.

    Returns:
        SandwichEmbeddings with all four vectors.
    """
    # Build the full text for the sandwich-level embedding
    full_text = (
        f"{assembled.bread_top} | {assembled.filling} | {assembled.bread_bottom}: "
        f"{assembled.description}"
    )

    texts = [
        assembled.bread_top,
        assembled.bread_bottom,
        assembled.filling,
        full_text,
    ]

    vectors = await embeddings.embed_batch(texts)

    return SandwichEmbeddings(
        bread_top=vectors[0],
        bread_bottom=vectors[1],
        filling=vectors[2],
        full=vectors[3],
    )


def _find_or_create_ingredient(
    text: str,
    ingredient_type: str,
    embedding: Optional[list[float]],
    sandwich_id: UUID,
    corpus: SandwichCorpus,
) -> CorpusIngredient:
    """Find an existing ingredient or create a new one.

    If a matching ingredient is found in the corpus, its usage_count is
    incremented. Otherwise a new CorpusIngredient is created and added.

    Args:
        text: Ingredient text.
        ingredient_type: 'bread' or 'filling'.
        embedding: Embedding vector (may be None).
        sandwich_id: ID of the sandwich using this ingredient.
        corpus: The sandwich corpus.

    Returns:
        The found or newly created CorpusIngredient.
    """
    existing = corpus.find_matching_ingredient(text, ingredient_type, embedding)
    if existing:
        existing.usage_count += 1
        logger.debug(
            "Reused ingredient '%s' (count=%d)", text[:40], existing.usage_count
        )
        return existing

    new_ing = CorpusIngredient(
        ingredient_id=uuid4(),
        text=text,
        ingredient_type=ingredient_type,
        embedding=embedding,
        usage_count=1,
    )
    corpus.add_ingredient(new_ing)
    logger.debug("Created new ingredient '%s'", text[:40])
    return new_ing


async def make_sandwich(
    content: str,
    source_metadata: SourceMetadata,
    corpus: SandwichCorpus,
    llm: SandwichLLM,
    embeddings: EmbeddingService,
    config: Optional[PipelineConfig] = None,
    on_stage: Optional[callable] = None,
) -> tuple[Optional[StoredSandwich], PipelineOutcome]:
    """Run the full sandwich-making pipeline.

    Pipeline stages:
        1. Preprocess content
        2. Identify candidate structures
        3. Select best candidate
        4. Assemble sandwich
        5. Validate sandwich
        6. Generate embeddings
        7. Store in corpus

    Args:
        content: Raw content string.
        source_metadata: Metadata about the content source.
        corpus: The sandwich corpus for novelty/reuse checks.
        llm: LLM service.
        embeddings: Embedding service.
        config: Pipeline configuration.

    Returns:
        Tuple of (StoredSandwich or None, PipelineOutcome describing result).
    """
    cfg = config or PipelineConfig()
    _notify = on_stage if on_stage else lambda stage: None

    # 1. Preprocess
    _notify("preprocess")
    prep_result = preprocess(
        content,
        content_type=source_metadata.content_type,
        config=cfg.preprocess,
    )
    if prep_result.skip:
        outcome = _log_pipeline_outcome(
            "preprocessing", "skipped", prep_result.skip_reason or "unknown"
        )
        return None, outcome

    # 2. Identify
    _notify("identify")
    id_result = await identify_ingredients(prep_result.text, llm)
    if not id_result.candidates:
        outcome = _log_pipeline_outcome(
            "identification",
            "no_candidates",
            id_result.no_sandwich_reason or "no viable structures",
        )
        return None, outcome

    # 3. Select
    _notify("select")
    corpus_embeddings = corpus.get_all_embeddings() if not corpus.is_empty() else None
    type_frequencies = corpus.get_type_frequencies() if not corpus.is_empty() else None

    selected = select_candidate(
        id_result.candidates,
        corpus_embeddings=corpus_embeddings,
        type_frequencies=type_frequencies,
        config=cfg.selection,
    )
    if not selected:
        outcome = _log_pipeline_outcome(
            "selection", "none_viable", "all candidates below threshold"
        )
        return None, outcome

    # 4. Assemble
    _notify("assemble")
    assembled = await assemble_sandwich(selected.candidate, prep_result.text, llm)

    # 5. Validate
    _notify("validate")
    validation = await validate_sandwich(
        name=assembled.name,
        bread_top=assembled.bread_top,
        bread_bottom=assembled.bread_bottom,
        filling=assembled.filling,
        structure_type=assembled.structure_type,
        description=assembled.description,
        containment_argument=assembled.containment_argument,
        llm=llm,
        embeddings=embeddings,
        corpus_embeddings=corpus_embeddings,
        config=cfg.validation,
    )
    if validation.recommendation == "reject":
        outcome = _log_pipeline_outcome(
            "validation", "rejected", validation.rationale
        )
        return None, outcome

    # 6. Generate embeddings
    _notify("embeddings")
    sandwich_embeddings = await generate_sandwich_embeddings(assembled, embeddings)

    # 7. Store — create ingredients and update corpus
    sandwich_id = uuid4()

    bread_top_ing = _find_or_create_ingredient(
        assembled.bread_top, "bread", sandwich_embeddings.bread_top, sandwich_id, corpus
    )
    bread_bottom_ing = _find_or_create_ingredient(
        assembled.bread_bottom, "bread", sandwich_embeddings.bread_bottom, sandwich_id, corpus
    )
    filling_ing = _find_or_create_ingredient(
        assembled.filling, "filling", sandwich_embeddings.filling, sandwich_id, corpus
    )

    corpus.add_sandwich(sandwich_embeddings.full, assembled.structure_type)

    stored = StoredSandwich(
        sandwich_id=sandwich_id,
        assembled=assembled,
        validation=validation,
        embeddings=sandwich_embeddings,
        source_metadata=source_metadata,
        ingredients={
            "bread_top": bread_top_ing,
            "bread_bottom": bread_bottom_ing,
            "filling": filling_ing,
        },
    )

    outcome = _log_pipeline_outcome("storage", "success", str(sandwich_id))
    logger.info(
        "Sandwich '%s' stored (validity=%.3f, recommendation=%s)",
        assembled.name,
        validation.overall_score,
        validation.recommendation,
    )

    return stored, outcome
