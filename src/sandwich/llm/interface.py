"""Abstract interfaces for LLM and embedding services.

Reference: SPEC.md Sections 7.1, 7.2
"""

from abc import ABC, abstractmethod


class SandwichLLM(ABC):
    """Abstract base class for the LLM backend used by SANDWICH components.

    Each method corresponds to a specific stage of the sandwich-making
    pipeline. Implementations should handle prompt formatting, API calls,
    and basic response extraction. Prompt *content* is not defined here
    (that's for later prompts)—this is infrastructure only.
    """

    @abstractmethod
    async def generate_curiosity(self, recent_topics: list[str]) -> str:
        """Generate a curiosity prompt for foraging.

        Args:
            recent_topics: Topics recently explored, to avoid repetition.

        Returns:
            A single-sentence curiosity prompt.
        """
        ...

    @abstractmethod
    async def identify_ingredients(self, content: str) -> str:
        """Identify candidate sandwich ingredients from content.

        Args:
            content: Preprocessed source content.

        Returns:
            Raw LLM response text (parsed by caller).
        """
        ...

    @abstractmethod
    async def assemble_sandwich(
        self,
        content: str,
        bread_top: str,
        bread_bottom: str,
        filling: str,
        structure_type: str,
    ) -> str:
        """Assemble a sandwich from selected ingredients.

        Args:
            content: Source content snippet.
            bread_top: Top bread concept.
            bread_bottom: Bottom bread concept.
            filling: Filling concept.
            structure_type: Structural type name.

        Returns:
            Raw LLM response text (parsed by caller).
        """
        ...

    @abstractmethod
    async def assess_quality(
        self,
        name: str,
        bread_top: str,
        bread_bottom: str,
        filling: str,
        structure_type: str,
        description: str,
        containment_argument: str,
    ) -> str:
        """Assess the quality/validity of an assembled sandwich.

        Args:
            name: Sandwich name.
            bread_top: Top bread concept.
            bread_bottom: Bottom bread concept.
            filling: Filling concept.
            structure_type: Structural type name.
            description: Sandwich description.
            containment_argument: Why the filling is contained.

        Returns:
            Raw LLM response text (parsed by caller).
        """
        ...

    @abstractmethod
    async def generate_commentary(self, sandwich_summary: str) -> str:
        """Generate Reuben's commentary on a sandwich.

        Args:
            sandwich_summary: Brief summary of the sandwich.

        Returns:
            Commentary text in Reuben's voice.
        """
        ...

    @abstractmethod
    async def raw_call(self, system_prompt: str, user_prompt: str) -> str:
        """Make a raw LLM call with explicit system/user prompts.

        This is useful for parse_with_recovery retries and ad-hoc calls.

        Args:
            system_prompt: System prompt text.
            user_prompt: User prompt text.

        Returns:
            Raw response text.
        """
        ...


class EmbeddingService(ABC):
    """Abstract base class for embedding generation."""

    @abstractmethod
    async def embed_single(self, text: str) -> list[float]:
        """Generate an embedding for a single text.

        Args:
            text: The text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors, one per input text.
        """
        ...
