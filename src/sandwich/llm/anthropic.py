"""Anthropic Claude implementation of the SandwichLLM interface.

Reference: SPEC.md Sections 7.1, 7.2
"""

import logging
from pathlib import Path
from typing import Optional

import anthropic

from sandwich.config import LLMConfig
from sandwich.errors.exceptions import FatalError, RetryableError
from sandwich.llm.interface import SandwichLLM
from sandwich.llm.retry import RetryConfig, with_retry
from sandwich.observability.logging import NullObserver, hash_prompt

logger = logging.getLogger(__name__)

# Resolve prompt templates relative to the project root
_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")


class AnthropicSandwichLLM(SandwichLLM):
    """SandwichLLM backed by the Anthropic Messages API."""

    def __init__(
        self,
        config: LLMConfig | None = None,
        observer: object | None = None,
        retry_config: RetryConfig | None = None,
        max_tokens: int = 4096,
    ):
        self.config = config or LLMConfig()
        self.observer = observer or NullObserver()
        self.retry_config = retry_config or RetryConfig()
        self.max_tokens = max_tokens
        self._client_instance: anthropic.Anthropic | None = None

    @property
    def _client(self) -> anthropic.Anthropic:
        """Lazily initialize the Anthropic client."""
        if self._client_instance is None:
            self._client_instance = anthropic.Anthropic()
        return self._client_instance

    # -- internal helpers --------------------------------------------------

    async def _call(
        self,
        system_prompt: str,
        user_prompt: str,
        component: str = "raw",
    ) -> str:
        """Make a single API call with retry and observability."""
        prompt_h = hash_prompt(system_prompt + user_prompt)
        start = self.observer.on_call_start(component, prompt_h)

        async def _do_call() -> str:
            try:
                message = self._client.messages.create(
                    model=self.config.model,
                    max_tokens=self.max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                return message  # type: ignore[return-value]
            except anthropic.RateLimitError as e:
                raise RetryableError(
                    str(e), reason="rate_limit"
                ) from e
            except anthropic.APIConnectionError as e:
                raise RetryableError(
                    str(e), reason="network"
                ) from e
            except anthropic.APITimeoutError as e:
                raise RetryableError(
                    str(e), reason="timeout"
                ) from e
            except anthropic.AuthenticationError as e:
                raise FatalError(
                    str(e), reason="auth_error"
                ) from e
            except anthropic.APIStatusError as e:
                if e.status_code and e.status_code >= 500:
                    raise RetryableError(
                        str(e), reason="network"
                    ) from e
                raise FatalError(
                    str(e), reason="unknown"
                ) from e

        error_str: Optional[str] = None
        try:
            message = await with_retry(_do_call, config=self.retry_config)
            text = message.content[0].text
            input_tokens = message.usage.input_tokens
            output_tokens = message.usage.output_tokens
            return text
        except Exception as e:
            error_str = str(e)
            raise
        finally:
            self.observer.on_call_end(
                component=component,
                model=self.config.model,
                prompt_hash=prompt_h,
                start_time=start,
                input_tokens=input_tokens if error_str is None else 0,
                output_tokens=output_tokens if error_str is None else 0,
                error=error_str,
            )

    # -- SandwichLLM interface ---------------------------------------------

    async def generate_curiosity(self, recent_topics: list[str]) -> str:
        preamble = _load_prompt("personality_preamble.txt").strip()
        template = _load_prompt("curiosity.txt")
        topics_str = ", ".join(recent_topics) if recent_topics else "none yet"
        user = template.format(recent_topics=topics_str)
        return await self._call(preamble, user, component="curiosity")

    async def identify_ingredients(self, content: str) -> str:
        preamble = _load_prompt("personality_preamble.txt").strip()
        template = _load_prompt("identifier.txt")
        user = template.format(content=content)
        return await self._call(preamble, user, component="identifier")

    async def assemble_sandwich(
        self,
        content: str,
        bread_top: str,
        bread_bottom: str,
        filling: str,
        structure_type: str,
    ) -> str:
        preamble = _load_prompt("personality_preamble.txt").strip()
        template = _load_prompt("assembler.txt")
        user = template.format(
            content=content[:500],
            bread_top=bread_top,
            bread_bottom=bread_bottom,
            filling=filling,
            structure_type=structure_type,
        )
        return await self._call(preamble, user, component="assembler")

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
        template = _load_prompt("validator.txt")
        user = template.format(
            name=name,
            bread_top=bread_top,
            bread_bottom=bread_bottom,
            filling=filling,
            structure_type=structure_type,
            description=description,
            containment_argument=containment_argument,
        )
        return await self._call(
            "You are evaluating a sandwich for validity and quality.",
            user,
            component="validator",
        )

    async def generate_commentary(self, sandwich_summary: str) -> str:
        system = (
            "You are Sandy. Reflect briefly on this sandwich in your "
            "characteristic voice: content, dry wit, philosophical depth."
        )
        user = f"Sandwich summary:\n{sandwich_summary}"
        return await self._call(system, user, component="commentary")

    async def raw_call(self, system_prompt: str, user_prompt: str) -> str:
        return await self._call(system_prompt, user_prompt, component="raw")
