"""Entry point for Sandy – the sandwich-making agent.

Usage:
    python -m sandwich.main --max-sandwiches 5
    python -m sandwich.main --max-duration 30

Reference: PROMPTS.md Prompt 10
"""

import argparse
import asyncio
import hashlib
import logging
from datetime import timedelta
from typing import Optional

from sandwich.agent.forager import Forager, ForagerConfig
from sandwich.agent.pipeline import StoredSandwich
from sandwich.agent.sandy import Sandy
from sandwich.config import SandwichConfig
from sandwich.db.corpus import CorpusIngredient, SandwichCorpus
from sandwich.db.models import Ingredient, Sandwich, SandwichIngredient, Source
from sandwich.db.repository import Repository
from sandwich.llm.anthropic import AnthropicSandwichLLM
from sandwich.llm.embeddings import OpenAIEmbeddingService
from sandwich.sources.web_search import WebSearchSource
from sandwich.sources.wikipedia import WikipediaSource

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _load_corpus_from_db(repo: Repository) -> SandwichCorpus:
    """Load existing sandwiches from DB into an in-memory corpus."""
    corpus = SandwichCorpus()
    sandwiches = repo.get_all_sandwiches()
    for s in sandwiches:
        # Try to load the embedding; skip if not available
        emb = repo.get_sandwich_embeddings(s.sandwich_id)
        if emb:
            corpus.add_sandwich(emb, s.structural_type_id or 0)
    corpus.total_sandwiches = len(sandwiches)
    logger.info("Loaded %d sandwiches from database into corpus", len(sandwiches))
    return corpus


def _make_db_persister(repo: Repository, type_cache: dict[str, int]):
    """Create a callback that persists a StoredSandwich to the database."""

    def persist(stored: StoredSandwich) -> None:
        sw = stored.assembled
        v = stored.validation

        # Insert source
        content_hash = hashlib.sha256(
            (stored.source_metadata.url or "").encode()
        ).hexdigest()[:16]
        source = Source(
            url=stored.source_metadata.url,
            domain=stored.source_metadata.domain,
            content_type=stored.source_metadata.content_type,
            content_hash=content_hash,
        )
        source_id = repo.insert_source(source)

        # Look up structural type ID
        type_id = type_cache.get(sw.structure_type)
        if type_id is None:
            st = repo.get_structural_type_by_name(sw.structure_type)
            if st and st.type_id:
                type_id = st.type_id
                type_cache[sw.structure_type] = type_id

        # Insert sandwich
        sandwich = Sandwich(
            sandwich_id=stored.sandwich_id,
            name=sw.name,
            description=sw.description,
            bread_top=sw.bread_top,
            bread_bottom=sw.bread_bottom,
            filling=sw.filling,
            validity_score=v.overall_score,
            bread_compat_score=v.bread_compat_score,
            containment_score=v.containment_score,
            specificity_score=v.specificity_score,
            nontrivial_score=v.nontrivial_score,
            novelty_score=v.novelty_score,
            source_id=source_id,
            structural_type_id=type_id,
            assembly_rationale=sw.containment_argument,
            validation_rationale=v.rationale,
            sandy_commentary=sw.sandy_commentary,
        )
        repo.insert_sandwich(sandwich)

        # Store embeddings
        emb = stored.embeddings
        repo.update_sandwich_embeddings(
            stored.sandwich_id,
            emb.bread_top,
            emb.bread_bottom,
            emb.filling,
            emb.full,
        )

        # Insert ingredients
        for role, ing in stored.ingredients.items():
            db_ing = Ingredient(
                ingredient_id=ing.ingredient_id,
                text=ing.text,
                ingredient_type=ing.ingredient_type,
                first_seen_sandwich=stored.sandwich_id,
                usage_count=ing.usage_count,
            )
            try:
                repo.insert_ingredient(db_ing)
            except Exception:
                pass  # May already exist from a previous run

            link = SandwichIngredient(
                sandwich_id=stored.sandwich_id,
                ingredient_id=ing.ingredient_id,
                role=role,
            )
            repo.link_sandwich_ingredient(link)

        logger.info(
            "Persisted sandwich '%s' (%s) to database",
            sw.name,
            stored.sandwich_id,
        )

    return persist


def build_sandy(
    config: SandwichConfig,
    repo: Optional[Repository] = None,
) -> Sandy:
    """Construct a fully-wired Sandy agent."""
    llm = AnthropicSandwichLLM(config=config.llm)
    embeddings = OpenAIEmbeddingService()

    # Load corpus from DB if available, otherwise empty
    if repo:
        corpus = _load_corpus_from_db(repo)
    else:
        corpus = SandwichCorpus()

    sources = {}
    if config.foraging.wikipedia_enabled:
        sources.setdefault(1, []).append(WikipediaSource())
    if config.foraging.web_search_enabled:
        sources.setdefault(2, []).append(WebSearchSource())

    forager = Forager(
        sources=sources,
        llm=llm,
        config=ForagerConfig(max_patience=config.foraging.max_patience),
    )

    # DB persistence callback
    on_stored = None
    if repo:
        type_cache: dict[str, int] = {}
        on_stored = _make_db_persister(repo, type_cache)

    return Sandy(
        config=config,
        llm=llm,
        embeddings=embeddings,
        forager=forager,
        corpus=corpus,
        on_sandwich_stored=on_stored,
    )


async def main() -> None:
    parser = argparse.ArgumentParser(description="Sandy makes sandwiches")
    parser.add_argument(
        "--max-sandwiches", type=int, default=None,
        help="Stop after N sandwiches",
    )
    parser.add_argument(
        "--max-duration", type=int, default=None,
        help="Stop after N minutes",
    )
    parser.add_argument(
        "--no-db", action="store_true",
        help="Run without database persistence (in-memory only)",
    )
    args = parser.parse_args()

    config = SandwichConfig()

    # Connect to database unless --no-db
    repo = None
    if not args.no_db:
        try:
            repo = Repository(config.database.url)
            repo.connect()
            logger.info("Connected to database: %s", config.database.url)
        except Exception as e:
            logger.warning("Could not connect to database: %s (running in-memory)", e)
            repo = None

    Sandy = build_sandy(config, repo=repo)

    session = await Sandy.run(
        max_sandwiches=args.max_sandwiches,
        max_duration=timedelta(minutes=args.max_duration) if args.max_duration else None,
    )

    # Close DB connection
    if repo:
        repo.close()

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"  SESSION SUMMARY")
    print(f"{'=' * 60}")
    print(f"Session ID: {session.session_id}")
    print(f"Duration:   {session.ended_at - session.started_at}")
    print(f"Sandwiches: {session.sandwiches_made}")
    print(f"Attempts:   {session.foraging_attempts}")
    if repo:
        print(f"Database:   connected (sandwiches persisted)")
    else:
        print(f"Database:   not connected (in-memory only)")

    if session.sandwiches:
        for i, s in enumerate(session.sandwiches, 1):
            sw = s.assembled
            v = s.validation
            print(f"\n{'─' * 60}")
            print(f"  SANDWICH #{i}: {sw.name}")
            print(f"{'─' * 60}")
            print(f"  Structure:    {sw.structure_type}")
            print(f"  Bread Top:    {sw.bread_top}")
            print(f"  Filling:      {sw.filling}")
            print(f"  Bread Bottom: {sw.bread_bottom}")
            print(f"  Validity:     {v.overall_score:.2f} ({v.recommendation})")
            print(f"    Bread Compat:  {v.bread_compat_score:.2f}")
            print(f"    Containment:   {v.containment_score:.2f}")
            print(f"    Specificity:   {v.specificity_score:.2f}")
            print(f"    Nontrivial:    {v.nontrivial_score:.2f}")
            print(f"    Novelty:       {v.novelty_score:.2f}")
            print(f"\n  Description:")
            print(f"    {sw.description}")
            print(f"\n  Containment Argument:")
            print(f"    {sw.containment_argument}")
            print(f"\n  Sandy's Commentary:")
            print(f"    {sw.sandy_commentary}")

    print(f"\n{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
