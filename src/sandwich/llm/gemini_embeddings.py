"""Google Gemini embeddings service.

Uses Gemini's text-embedding-004 model for free embeddings.
"""

import logging
from typing import List

import google.generativeai as genai

from sandwich.llm.interface import EmbeddingService

logger = logging.getLogger(__name__)


class GeminiEmbeddingService(EmbeddingService):
    """Gemini implementation of the EmbeddingService interface.

    Uses text-embedding-004 model which is free and produces 768-dimensional vectors.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "models/text-embedding-004",
    ):
        """Initialize Gemini embeddings service.

        Args:
            api_key: Google AI API key
            model: Gemini embedding model to use
        """
        self.api_key = api_key
        self.model_name = model

        # Configure Gemini
        genai.configure(api_key=api_key)

    async def embed_single(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (768 dimensions)
        """
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            logger.error("Gemini embedding failed: %s", e)
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts in a single batch.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            # Gemini supports batch embedding
            result = genai.embed_content(
                model=self.model_name,
                content=texts,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            logger.error("Gemini batch embedding failed: %s", e)
            raise

    def get_dimension(self) -> int:
        """Get the dimensionality of embeddings.

        Returns:
            768 for text-embedding-004
        """
        return 768
