"""Google Gemini LLM client for sandwich-making.

Uses Gemini 2.0 Flash for cost-effective sandwich generation.
"""

import json
import logging
from typing import Any, Optional

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from sandwich.llm.interface import LLMCall, LLMResponse, SandwichLLM

logger = logging.getLogger(__name__)


class GeminiSandwichLLM(SandwichLLM):
    """Gemini implementation of the SandwichLLM interface.

    Uses Gemini 2.0 Flash for cost-effective, fast generation.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash-exp",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """Initialize Gemini client.

        Args:
            api_key: Google AI API key
            model: Gemini model to use (default: gemini-2.0-flash-exp)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
        """
        self.api_key = api_key
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    async def call(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Optional[dict[str, Any]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Make an LLM API call using Gemini.

        Args:
            system_prompt: System instructions
            user_prompt: User message
            response_schema: Optional JSON schema for structured output
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            LLMResponse with the generated text and token usage
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens

        try:
            # Combine system and user prompts
            # Gemini doesn't have separate system/user like Claude
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"

            # Configure generation
            generation_config = GenerationConfig(
                temperature=temp,
                max_output_tokens=max_tok,
            )

            # If response_schema is provided, use JSON mode
            if response_schema:
                generation_config.response_mime_type = "application/json"
                # Add schema instruction to prompt
                schema_str = json.dumps(response_schema, indent=2)
                combined_prompt += f"\n\nRespond with valid JSON matching this schema:\n{schema_str}"

            # Make the API call (synchronous - Gemini SDK doesn't have good async yet)
            response = self.model.generate_content(
                combined_prompt,
                generation_config=generation_config
            )

            # Extract text
            text = response.text

            # Parse token usage
            # Gemini's usage metadata is in response.usage_metadata
            input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
            output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)

            logger.info(
                "Gemini call: model=%s, temp=%.2f, tokens=%d/%d",
                self.model_name,
                temp,
                input_tokens,
                output_tokens,
            )

            return LLMResponse(
                text=text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model=self.model_name,
            )

        except Exception as e:
            logger.error("Gemini API call failed: %s", e)
            raise

    async def call_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Optional[dict[str, Any]] = None,
        max_retries: int = 3,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Make an LLM call with automatic retries on failure.

        Args:
            system_prompt: System instructions
            user_prompt: User message
            response_schema: Optional JSON schema for structured output
            max_retries: Maximum retry attempts
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            LLMResponse with the generated text and token usage
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                return await self.call(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response_schema=response_schema,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as e:
                last_error = e
                logger.warning(
                    "Gemini call failed (attempt %d/%d): %s",
                    attempt + 1,
                    max_retries,
                    e,
                )
                if attempt < max_retries - 1:
                    # Exponential backoff
                    import asyncio
                    await asyncio.sleep(2 ** attempt)

        # All retries exhausted
        raise RuntimeError(
            f"Gemini call failed after {max_retries} attempts"
        ) from last_error
