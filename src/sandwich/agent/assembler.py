"""Sandwich assembler – constructs a complete sandwich from selected ingredients.

Takes a candidate structure and source content, then uses the LLM to produce
a named, described sandwich with Sandy's commentary.

Reference: SPEC.md Section 3.2.5, 14.4; PROMPTS.md Prompt 6
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional

from sandwich.agent.identifier import CandidateStructure
from sandwich.llm.interface import SandwichLLM
from sandwich.llm.retry import parse_with_recovery

logger = logging.getLogger(__name__)

_PROMPT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "prompts")
_ASSEMBLER_PROMPT_PATH = os.path.join(_PROMPT_DIR, "assembler.txt")
_PERSONALITY_PREAMBLE_PATH = os.path.join(_PROMPT_DIR, "personality_preamble.txt")


@dataclass
class AssembledSandwich:
    """A fully assembled sandwich ready for validation."""

    name: str
    description: str
    containment_argument: str
    sandy_commentary: str
    bread_top: str
    bread_bottom: str
    filling: str
    structure_type: str
    source_content_snippet: str  # First 500 chars of source


def _load_prompt(path: str) -> str:
    """Load a prompt template from disk."""
    with open(path, "r") as f:
        return f.read()


async def assemble_sandwich(
    candidate: CandidateStructure,
    source_content: str,
    llm: SandwichLLM,
) -> AssembledSandwich:
    """Assemble a sandwich from a candidate and source content.

    Args:
        candidate: The selected candidate structure.
        source_content: The preprocessed source content.
        llm: LLM service for assembly.

    Returns:
        AssembledSandwich with all fields populated.
    """
    personality = _load_prompt(_PERSONALITY_PREAMBLE_PATH)
    assembler_template = _load_prompt(_ASSEMBLER_PROMPT_PATH)

    snippet = source_content[:500]

    user_prompt = assembler_template.format(
        content=snippet,
        bread_top=candidate.bread_top,
        bread_bottom=candidate.bread_bottom,
        filling=candidate.filling,
        structure_type=candidate.structure_type,
    )

    raw_response = await llm.assemble_sandwich(
        content=source_content,
        bread_top=candidate.bread_top,
        bread_bottom=candidate.bread_bottom,
        filling=candidate.filling,
        structure_type=candidate.structure_type,
    )

    # Recovery prompt for parse failures
    retry_prompt = (
        "Your previous response could not be parsed. "
        "Please respond ONLY with a valid JSON object with exactly these keys: "
        '"name" (string), "description" (string), "containment_argument" (string), '
        '"sandy_commentary" (string). No other text.'
    )

    async def _retry_call(rp: str) -> str:
        return await llm.raw_call(
            system_prompt=personality,
            user_prompt=rp,
        )

    parsed = await parse_with_recovery(
        raw_response,
        required_fields=["name", "description", "containment_argument", "sandy_commentary"],
        llm_call=_retry_call,
        retry_prompt=retry_prompt,
    )

    assembled = AssembledSandwich(
        name=str(parsed["name"]).strip(),
        description=str(parsed["description"]).strip(),
        containment_argument=str(parsed["containment_argument"]).strip(),
        sandy_commentary=str(parsed["sandy_commentary"]).strip(),
        bread_top=candidate.bread_top,
        bread_bottom=candidate.bread_bottom,
        filling=candidate.filling,
        structure_type=candidate.structure_type,
        source_content_snippet=snippet,
    )

    logger.info(
        "Assembled sandwich: '%s' (type=%s)",
        assembled.name,
        assembled.structure_type,
    )

    return assembled
