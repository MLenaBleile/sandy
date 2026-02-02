"""Content preprocessor pipeline.

Cleans, filters, and scores raw content before it reaches the identifier.

Reference: SPEC.md Section 3.2.2, PROMPTS.md Prompt 4
"""

import logging
import re
import string
from dataclasses import dataclass
from typing import Optional

from readability import Document as ReadabilityDocument
from bs4 import BeautifulSoup, Comment
from lingua import Language, LanguageDetectorBuilder

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-initialised language detector (expensive to build)
# ---------------------------------------------------------------------------
_lang_detector = None


def _get_lang_detector():
    global _lang_detector
    if _lang_detector is None:
        _lang_detector = (
            LanguageDetectorBuilder.from_all_languages()
            .with_preloaded_language_models()
            .build()
        )
    return _lang_detector


# ---------------------------------------------------------------------------
# Configurable boilerplate patterns
# ---------------------------------------------------------------------------
DEFAULT_BOILERPLATE_PATTERNS: list[str] = [
    # Cookie / privacy notices
    r"(?i)we use cookies[^.]*\.",
    r"(?i)cookie policy[^.]*\.",
    r"(?i)by (continuing|using) (this|our) (site|website)[^.]*\.",
    r"(?i)accept (all )?cookies[^.]*\.",
    r"(?i)privacy policy[^.]*\.",
    # Subscribe / newsletter prompts
    r"(?i)subscribe to our newsletter[^.]*\.",
    r"(?i)sign up for our[^.]*newsletter[^.]*\.",
    r"(?i)enter your email[^.]*\.",
    r"(?i)get (the latest|our) updates[^.]*\.",
    # Social-media CTAs
    r"(?i)follow us on[^.]*\.",
    r"(?i)share (this|on)[^.]*\.",
    # Navigation / footer boilerplate
    r"(?i)skip to (main )?content[^.]*\.",
    r"(?i)all rights reserved[^.]*\.",
    r"(?i)terms (of (use|service)|and conditions)[^.]*\.",
    r"(?i)copyright ©[^.]*\.",
]


@dataclass
class PreprocessConfig:
    """Tuneable knobs for the preprocessing pipeline."""

    min_length: int = 200
    max_length: int = 10000
    allowed_languages: list[str] | None = None  # None → ["en"]
    quality_threshold: float = 0.4
    boilerplate_patterns: list[str] | None = None  # None → defaults

    def __post_init__(self):
        if self.allowed_languages is None:
            self.allowed_languages = ["en"]
        if self.boilerplate_patterns is None:
            self.boilerplate_patterns = list(DEFAULT_BOILERPLATE_PATTERNS)


@dataclass
class PreprocessResult:
    """Output of the preprocessing pipeline."""

    text: Optional[str]
    skip: bool
    skip_reason: Optional[str]  # 'too_short', 'non_english', 'low_quality', 'boilerplate'
    quality_score: float
    original_length: int
    processed_length: int
    language: str


# ---------------------------------------------------------------------------
# Stage 1 – HTML extraction
# ---------------------------------------------------------------------------

def _extract_html(raw: str) -> str:
    """Use readability-lxml to pull the main article text from HTML."""
    doc = ReadabilityDocument(raw)
    html_summary = doc.summary()

    soup = BeautifulSoup(html_summary, "html.parser")

    # Strip comments
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    # Strip script / style leftovers
    for tag in soup.find_all(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    # Collapse excessive whitespace while preserving paragraph breaks
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Stage 2 – Boilerplate removal
# ---------------------------------------------------------------------------

def _remove_boilerplate(text: str, patterns: list[str]) -> str:
    """Remove common boilerplate sentences from text."""
    for pattern in patterns:
        text = re.sub(pattern, "", text)
    # Collapse leftover whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Stage 3 – Language detection
# ---------------------------------------------------------------------------

def _detect_language(text: str) -> str:
    """Return ISO 639-1 code (e.g. 'en', 'fr') for the dominant language."""
    detector = _get_lang_detector()
    result = detector.detect_language_of(text)
    if result is None:
        return "unknown"
    return result.iso_code_639_1.name.lower()


# ---------------------------------------------------------------------------
# Stage 4 – Length normalisation
# ---------------------------------------------------------------------------

def _normalise_length(
    text: str, min_length: int, max_length: int
) -> tuple[str, Optional[str]]:
    """Return (possibly-truncated text, skip_reason | None).

    Smart truncation: find the last sentence boundary before max_length.
    """
    if len(text) < min_length:
        return text, "too_short"

    if len(text) <= max_length:
        return text, None

    # Smart truncation – cut at last sentence boundary within max_length
    truncated = text[:max_length]
    # Look for the last sentence-ending punctuation followed by whitespace
    last_boundary = -1
    for m in re.finditer(r'[.!?][\s"]', truncated):
        last_boundary = m.end()

    if last_boundary > max_length * 0.5:
        return truncated[:last_boundary].rstrip(), None

    # Fallback: just cut at max_length
    return truncated.rstrip(), None


# ---------------------------------------------------------------------------
# Stage 5 – Quality assessment
# ---------------------------------------------------------------------------

def _compute_quality_score(text: str) -> float:
    """Heuristic quality score ∈ [0, 1] based on textual signals.

    Components (each 0-1, equally weighted):
      1. Sentence length variance  – high variance → diverse writing → good
      2. Unique word ratio          – > 0.3 good
      3. Punctuation density        – 0.02-0.08 sweet spot
      4. Has multiple paragraphs    – 1.0 if yes, 0.0 if no
    """
    if not text:
        return 0.0

    # --- Sentence length variance ---
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) < 2:
        variance_score = 0.0
    else:
        lengths = [len(s.split()) for s in sentences]
        mean_len = sum(lengths) / len(lengths)
        variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
        # Normalise: variance of 50+ words² is considered excellent
        variance_score = min(variance / 50.0, 1.0)

    # --- Unique word ratio ---
    words = text.lower().split()
    if not words:
        return 0.0
    unique_ratio = len(set(words)) / len(words)
    # Scale: 0.3 → 0.0, 0.7+ → 1.0
    unique_score = max(0.0, min((unique_ratio - 0.3) / 0.4, 1.0))

    # --- Punctuation density ---
    punct_count = sum(1 for c in text if c in string.punctuation)
    punct_density = punct_count / len(text) if text else 0
    # Sweet spot 0.02-0.08
    if 0.02 <= punct_density <= 0.08:
        punct_score = 1.0
    elif punct_density < 0.02:
        punct_score = punct_density / 0.02
    else:
        # Too much punctuation
        punct_score = max(0.0, 1.0 - (punct_density - 0.08) / 0.08)

    # --- Multiple paragraphs ---
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    para_score = 1.0 if len(paragraphs) > 1 else 0.0

    # Equal weighting
    return (variance_score + unique_score + punct_score + para_score) / 4.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def preprocess(
    content: str,
    *,
    content_type: str = "text",
    config: Optional[PreprocessConfig] = None,
) -> PreprocessResult:
    """Run the full preprocessing pipeline.

    Args:
        content: Raw content string.
        content_type: 'html' or 'text'.
        config: Optional preprocessing configuration.

    Returns:
        PreprocessResult with cleaned text or skip information.
    """
    cfg = config or PreprocessConfig()
    original_length = len(content)

    # Stage 1: HTML extraction
    if content_type.lower() == "html":
        text = _extract_html(content)
    else:
        text = content

    # Stage 2: Boilerplate removal
    text = _remove_boilerplate(text, cfg.boilerplate_patterns)

    # If basically nothing left after boilerplate removal, flag it
    if len(text.strip()) < cfg.min_length:
        return PreprocessResult(
            text=None,
            skip=True,
            skip_reason="boilerplate" if original_length >= cfg.min_length else "too_short",
            quality_score=0.0,
            original_length=original_length,
            processed_length=len(text),
            language="unknown",
        )

    # Stage 3: Language detection
    language = _detect_language(text)
    if language not in cfg.allowed_languages:
        return PreprocessResult(
            text=None,
            skip=True,
            skip_reason="non_english",
            quality_score=0.0,
            original_length=original_length,
            processed_length=len(text),
            language=language,
        )

    # Stage 4: Length normalisation
    text, length_skip = _normalise_length(text, cfg.min_length, cfg.max_length)
    if length_skip:
        return PreprocessResult(
            text=None,
            skip=True,
            skip_reason=length_skip,
            quality_score=0.0,
            original_length=original_length,
            processed_length=len(text),
            language=language,
        )

    # Stage 5: Quality assessment
    quality_score = _compute_quality_score(text)
    if quality_score < cfg.quality_threshold:
        return PreprocessResult(
            text=None,
            skip=True,
            skip_reason="low_quality",
            quality_score=quality_score,
            original_length=original_length,
            processed_length=len(text),
            language=language,
        )

    logger.info(
        "Preprocessed: %d→%d chars, lang=%s, quality=%.3f",
        original_length,
        len(text),
        language,
        quality_score,
    )

    return PreprocessResult(
        text=text,
        skip=False,
        skip_reason=None,
        quality_score=quality_score,
        original_length=original_length,
        processed_length=len(text),
        language=language,
    )
