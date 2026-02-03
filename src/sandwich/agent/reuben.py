"""Reuben – the sandwich-making agent.

Wires together the forager, pipeline, state machine, and personality
into a single autonomous agent.

Reference: SPEC.md Sections 6.5, 8; PROMPTS.md Prompt 10
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Optional
from uuid import UUID, uuid4

from sandwich.agent.error_handler import determine_recovery_event
from sandwich.agent.forager import Forager
from sandwich.agent.pipeline import (
    PipelineConfig,
    SourceMetadata,
    StoredSandwich,
    make_sandwich,
)
from sandwich.agent.state_machine import AgentState, StateMachine
from sandwich.config import SandwichConfig
from sandwich.db.corpus import SandwichCorpus
from sandwich.errors.exceptions import FatalError, SandwichError
from sandwich.llm.interface import EmbeddingService, SandwichLLM

logger = logging.getLogger(__name__)


@dataclass
class Session:
    """A Reuben working session."""

    session_id: UUID = field(default_factory=uuid4)
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    sandwiches_made: int = 0
    foraging_attempts: int = 0
    messages: list[str] = field(default_factory=list)
    sandwiches: list[StoredSandwich] = field(default_factory=list)


# --- Reuben's voice messages ---

VOICE_SESSION_START = (
    "The morning is fresh. The internet is vast. "
    "Somewhere in it: bread."
)

VOICE_SESSION_END = (
    "A good session. I rest now. "
    "The sandwiches wait for no one, but they are patient."
)

VOICE_SUCCESS = (
    "Another sandwich, complete. The corpus grows. "
    "Structure emerges from the formless."
)

VOICE_NO_CONTENT = (
    "The kitchen is closed. I wait. The bread does not spoil."
)

VOICE_NO_CANDIDATES = (
    "All filling, no structure. A soup. I make sandwiches, not soups."
)

VOICE_REJECTED = (
    "I could force this. But a forced sandwich nourishes no one. I let it go."
)

VOICE_PATIENCE_EXHAUSTED = (
    "Patience is a virtue, but even Reuben has limits. "
    "Tomorrow the internet will have new bread."
)


class Reuben:
    """The sandwich-making agent."""

    def __init__(
        self,
        config: SandwichConfig,
        llm: SandwichLLM,
        embeddings: EmbeddingService,
        forager: Forager,
        corpus: Optional[SandwichCorpus] = None,
        emit_fn: Optional[Callable[[str], None]] = None,
        on_sandwich_stored: Optional[Callable[["StoredSandwich"], None]] = None,
    ):
        self.config = config
        self.llm = llm
        self.embeddings = embeddings
        self.forager = forager
        self.corpus = corpus or SandwichCorpus()
        self.state_machine = StateMachine()
        self.session: Optional[Session] = None
        self.patience: int = config.foraging.max_patience
        self.recent_topics: list[str] = []
        self._emit_fn = emit_fn or (lambda msg: print(f"[Reuben] {msg}"))
        self._on_sandwich_stored = on_sandwich_stored

    def emit(self, message: str) -> None:
        """Output a message in Reuben's voice."""
        self._emit_fn(message)
        if self.session:
            self.session.messages.append(message)
        logger.info("Reuben: %s", message)

    def start_session(self) -> Session:
        """Create and start a new session."""
        self.session = Session()
        self.state_machine = StateMachine(session_id=self.session.session_id)
        self.patience = self.config.foraging.max_patience
        self.emit(VOICE_SESSION_START)
        return self.session

    async def run(
        self,
        max_sandwiches: Optional[int] = None,
        max_duration: Optional[timedelta] = None,
    ) -> Session:
        """Main autonomous loop.

        Runs until patience is exhausted, max sandwiches reached,
        max duration exceeded, or a fatal error occurs.

        Args:
            max_sandwiches: Stop after making this many sandwiches.
            max_duration: Stop after this duration.

        Returns:
            The completed session.
        """
        if not self.session:
            self.start_session()

        while not self._should_stop(max_sandwiches, max_duration):
            try:
                await self.run_one_cycle()
            except FatalError as e:
                self.state_machine.transition("error")
                event = determine_recovery_event(e)
                self.state_machine.transition(event)
                self.emit(VOICE_NO_CONTENT)
                break
            except SandwichError as e:
                # Non-fatal errors: recover and continue
                if self.state_machine.can_transition("error"):
                    self.state_machine.transition("error")
                    event = determine_recovery_event(e)
                    self.state_machine.transition(event)
                self.patience -= 1
                self.forager.record_failure()

        self.end_session()
        return self.session

    async def run_one_cycle(self) -> Optional[StoredSandwich]:
        """Run one forage → make_sandwich cycle.

        Returns:
            StoredSandwich if successful, None otherwise.
        """
        session = self.session

        # Forage
        self.state_machine.transition("start_foraging")
        session.foraging_attempts += 1

        curiosity = await self.forager.generate_curiosity(self.recent_topics)
        result = await self.forager.forage(curiosity)

        if result is None or not result.source_result.content:
            self.state_machine.transition("forage_failed")
            self.emit(VOICE_NO_CONTENT)
            self.patience -= 1
            self.forager.record_failure()
            return None

        self.recent_topics.append(curiosity[:100])
        if len(self.recent_topics) > 20:
            self.recent_topics = self.recent_topics[-20:]

        # Run pipeline
        self.state_machine.transition("content_found")

        source_metadata = SourceMetadata(
            url=result.source_result.url,
            domain=result.source_result.metadata.get("source", result.source_name),
            content_type=result.source_result.content_type,
        )

        pipeline_config = PipelineConfig()

        stored, outcome = await make_sandwich(
            content=result.source_result.content,
            source_metadata=source_metadata,
            corpus=self.corpus,
            llm=self.llm,
            embeddings=self.embeddings,
            config=pipeline_config,
        )

        # Map pipeline outcome to state transitions
        if outcome.stage == "preprocessing":
            self.state_machine.transition("content_rejected")
            self.emit(VOICE_NO_CONTENT)
            self.patience -= 1
            self.forager.record_failure()
            return None

        # Move through remaining states (the pipeline already did the work)
        self.state_machine.transition("content_accepted")

        if outcome.stage == "identification":
            self.state_machine.transition("no_candidates")
            self.emit(VOICE_NO_CANDIDATES)
            self.patience -= 1
            self.forager.record_failure()
            return None

        self.state_machine.transition("candidates_found")

        if outcome.stage == "selection":
            self.state_machine.transition("none_viable")
            self.emit(VOICE_NO_CANDIDATES)
            self.patience -= 1
            self.forager.record_failure()
            return None

        self.state_machine.transition("candidate_selected")
        self.state_machine.transition("assembly_complete")

        if outcome.stage == "validation" and outcome.outcome == "rejected":
            self.state_machine.transition("rejected")
            self.emit(VOICE_REJECTED)
            self.patience -= 1
            self.forager.record_failure()
            return None

        if stored is not None:
            self.state_machine.transition("accepted")
            self.state_machine.transition("stored")

            session.sandwiches_made += 1
            session.sandwiches.append(stored)
            self.patience = self.config.foraging.max_patience
            self.forager.record_success()

            # Persist to database if callback provided
            if self._on_sandwich_stored:
                try:
                    self._on_sandwich_stored(stored)
                except Exception as e:
                    logger.warning("Failed to persist sandwich to DB: %s", e)

            self.emit(
                f"{VOICE_SUCCESS} '{stored.assembled.name}' — "
                f"validity {stored.validation.overall_score:.2f}."
            )
            return stored

        # Shouldn't reach here, but handle gracefully
        if self.state_machine.can_transition("rejected"):
            self.state_machine.transition("rejected")
        self.patience -= 1
        self.forager.record_failure()
        return None

    def end_session(self) -> None:
        """End the current session."""
        if not self.session:
            return

        self.session.ended_at = datetime.now()

        if self.patience <= 0:
            self.emit(VOICE_PATIENCE_EXHAUSTED)

        self.emit(VOICE_SESSION_END)

        # Transition to session end if possible
        if self.state_machine.current_state != AgentState.SESSION_END:
            if self.state_machine.can_transition("end_session"):
                self.state_machine.transition("end_session")

        logger.info(
            "Session %s ended: %d sandwiches from %d attempts",
            self.session.session_id,
            self.session.sandwiches_made,
            self.session.foraging_attempts,
        )

    def _should_stop(
        self,
        max_sandwiches: Optional[int],
        max_duration: Optional[timedelta],
    ) -> bool:
        """Check whether the agent should stop."""
        if self.patience <= 0:
            return True
        if self.state_machine.current_state == AgentState.SESSION_END:
            return True
        if max_sandwiches and self.session and self.session.sandwiches_made >= max_sandwiches:
            return True
        if max_duration and self.session:
            elapsed = datetime.now() - self.session.started_at
            if elapsed >= max_duration:
                return True
        return False
