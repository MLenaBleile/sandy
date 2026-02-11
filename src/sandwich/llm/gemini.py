"""Google Gemini LLM client for sandwich-making.

Uses Gemini 2.0 Flash for cost-effective sandwich generation.
"""

import logging
from typing import Any, Optional

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from sandwich.llm.interface import SandwichLLM

logger = logging.getLogger(__name__)


class GeminiSandwichLLM(SandwichLLM):
    """Gemini implementation of the SandwichLLM interface.

    Uses Gemini 2.0 Flash for cost-effective, fast generation.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
    ):
        """Initialize Gemini client.

        Args:
            api_key: Google AI API key
            model: Gemini model to use (default: gemini-1.5-flash)
            temperature: Sampling temperature (0.0-1.0)
        """
        self.api_key = api_key
        self.model_name = model
        self.temperature = temperature

        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    async def generate_curiosity(self, recent_topics: list[str]) -> str:
        """Generate a curiosity prompt for foraging."""
        # Load curiosity prompt from prompts/curiosity.txt
        from pathlib import Path
        prompt_file = Path(__file__).parent.parent.parent.parent / "prompts" / "curiosity.txt"
        system_prompt = prompt_file.read_text()

        user_prompt = f"Recent topics explored: {', '.join(recent_topics) if recent_topics else 'None'}"
        return await self.raw_call(system_prompt, user_prompt)

    async def identify_ingredients(self, content: str) -> str:
        """Identify candidate sandwich ingredients from content."""
        from pathlib import Path
        prompt_file = Path(__file__).parent.parent.parent.parent / "prompts" / "identifier.txt"
        system_prompt = prompt_file.read_text()

        return await self.raw_call(system_prompt, content)

    async def assemble_sandwich(
        self,
        content: str,
        bread_top: str,
        bread_bottom: str,
        filling: str,
        structure_type: str,
    ) -> str:
        """Assemble a sandwich from selected ingredients."""
        from pathlib import Path
        prompt_file = Path(__file__).parent.parent.parent.parent / "prompts" / "assembler.txt"
        system_prompt = prompt_file.read_text()

        user_prompt = f"""Content: {content}

Bread Top: {bread_top}
Bread Bottom: {bread_bottom}
Filling: {filling}
Structure Type: {structure_type}"""

        return await self.raw_call(system_prompt, user_prompt)

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
        """Assess the quality/validity of an assembled sandwich."""
        from pathlib import Path
        prompt_file = Path(__file__).parent.parent.parent.parent / "prompts" / "validator.txt"
        system_prompt = prompt_file.read_text()

        user_prompt = f"""Name: {name}
Bread Top: {bread_top}
Bread Bottom: {bread_bottom}
Filling: {filling}
Structure Type: {structure_type}
Description: {description}
Containment Argument: {containment_argument}"""

        return await self.raw_call(system_prompt, user_prompt)

    async def generate_commentary(self, sandwich_summary: str) -> str:
        """Generate Sandy's commentary on a sandwich."""
        from pathlib import Path
        prompt_file = Path(__file__).parent.parent.parent.parent / "prompts" / "personality_preamble.txt"
        system_prompt = prompt_file.read_text()

        user_prompt = f"Provide a brief commentary on this sandwich: {sandwich_summary}"
        return await self.raw_call(system_prompt, user_prompt)

    async def raw_call(self, system_prompt: str, user_prompt: str) -> str:
        """Make a raw LLM call with explicit system/user prompts."""
        try:
            # Combine system and user prompts (Gemini doesn't separate them)
            combined_prompt = f"{system_prompt}\n\n{user_prompt}"

            # Configure generation
            generation_config = GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=4096,
            )

            # Make the API call (synchronous - Gemini SDK doesn't have good async yet)
            response = self.model.generate_content(
                combined_prompt,
                generation_config=generation_config
            )

            # Extract text
            text = response.text

            logger.info(
                "Gemini call: model=%s, temp=%.2f, tokens=%d/%d",
                self.model_name,
                self.temperature,
                getattr(response.usage_metadata, 'prompt_token_count', 0),
                getattr(response.usage_metadata, 'candidates_token_count', 0),
            )

            return text

        except Exception as e:
            logger.error("Gemini API call failed: %s", e)
            raise
