"""Tests for the content preprocessor pipeline.

Reference: PROMPTS.md Prompt 4
"""

import textwrap

import pytest

from sandwich.agent.preprocessor import (
    PreprocessConfig,
    PreprocessResult,
    _compute_quality_score,
    _extract_html,
    _normalise_length,
    _remove_boilerplate,
    _detect_language,
    preprocess,
    DEFAULT_BOILERPLATE_PATTERNS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_HTML = textwrap.dedent("""\
    <!DOCTYPE html>
    <html>
    <head><title>Squeeze Theorem - Wikipedia</title></head>
    <body>
    <nav><ul><li>Home</li><li>About</li><li>Contact</li></ul></nav>
    <div id="mw-content-text">
    <p>In calculus, the <b>squeeze theorem</b> (also known as the sandwich theorem)
    is a theorem regarding the limit of a function that is trapped between two
    other functions.</p>
    <p>The squeeze theorem is formally stated as follows. Let I be an interval
    containing the point a. Let g, f, and h be functions defined on I, except
    possibly at a itself. Suppose that for every x in I not equal to a, we have
    g(x) &le; f(x) &le; h(x), and also suppose that the limits of g and h as x
    approaches a are both equal to L. Then the limit of f as x approaches a is
    also equal to L.</p>
    <p>This theorem is particularly useful when direct computation of a limit is
    difficult. By bounding a function between two simpler functions whose limits
    are known, one can determine the limit of the more complex function. The
    theorem has applications in many areas of mathematics, including the
    evaluation of trigonometric limits and the proof of the continuity of certain
    functions.</p>
    </div>
    <footer>
    <p>All rights reserved. Copyright &copy; 2024 Wikipedia Foundation.</p>
    <p>Privacy policy. Terms of use.</p>
    </footer>
    <script>var tracking = true;</script>
    </body>
    </html>
""")

WELL_WRITTEN_ARTICLE = textwrap.dedent("""\
    The squeeze theorem, also known as the sandwich theorem, is a fundamental
    result in mathematical analysis. It provides a method for evaluating the
    limit of a function by bounding it between two other functions whose limits
    are already known.

    Formally, suppose that for all x in some interval containing c (except
    possibly at c itself), we have g(x) <= f(x) <= h(x). If both g(x) and h(x)
    approach the same limit L as x approaches c, then f(x) must also approach L.

    This theorem is particularly useful in situations where direct computation of
    a limit is difficult or impossible. For example, consider the well-known limit
    of sin(x)/x as x approaches 0. By establishing appropriate upper and lower
    bounds using geometric arguments on the unit circle, we can show that this
    limit equals 1.

    The applications of the squeeze theorem extend beyond elementary calculus.
    In real analysis, it plays a crucial role in proving the convergence of
    sequences and series. In probability theory, analogous bounding arguments
    appear in the proof of the law of large numbers. The versatility of this
    simple yet powerful tool makes it one of the cornerstones of mathematical
    reasoning about limits and convergence.
""")

REPETITIVE_SPAM = (
    "buy now buy now buy now buy now great deal "
    "buy now buy now buy now buy now great deal "
    "buy now buy now buy now buy now great deal "
    "buy now buy now buy now buy now great deal "
    "buy now buy now buy now buy now great deal "
    "buy now buy now buy now buy now great deal "
    "buy now buy now buy now buy now great deal "
    "buy now buy now buy now buy now great deal "
) * 5

FRENCH_TEXT = textwrap.dedent("""\
    Le théorème des gendarmes est un résultat fondamental de l'analyse
    mathématique. Il permet de déterminer la limite d'une fonction en
    l'encadrant entre deux autres fonctions dont les limites sont connues.

    Plus précisément, si pour tout x dans un intervalle contenant c (sauf
    éventuellement en c lui-même), on a g(x) <= f(x) <= h(x), et si g(x)
    et h(x) tendent vers la même limite L quand x tend vers c, alors f(x)
    tend également vers L.

    Ce théorème est particulièrement utile dans les cas où le calcul direct
    d'une limite est difficile ou impossible. Il est largement utilisé en
    analyse réelle, en théorie des probabilités et dans de nombreux autres
    domaines des mathématiques.
""")


# ===================================================================
# test_html_extraction
# ===================================================================

class TestHtmlExtraction:
    """Stage 1: Verify article text is extracted and junk removed."""

    def test_extracts_article_body(self):
        text = _extract_html(SAMPLE_HTML)
        assert "squeeze theorem" in text.lower()
        assert "sandwich theorem" in text.lower()

    def test_strips_navigation(self):
        text = _extract_html(SAMPLE_HTML)
        # Nav items should not survive extraction
        assert "Home" not in text or "About" not in text

    def test_strips_script_tags(self):
        text = _extract_html(SAMPLE_HTML)
        assert "tracking" not in text

    def test_returns_string(self):
        text = _extract_html(SAMPLE_HTML)
        assert isinstance(text, str)
        assert len(text) > 100


# ===================================================================
# test_boilerplate_removal
# ===================================================================

class TestBoilerplateRemoval:
    """Stage 2: Common boilerplate sentences should be stripped."""

    def test_removes_subscribe_prompt(self):
        text = "Great article. Subscribe to our newsletter. More content here."
        cleaned = _remove_boilerplate(text, DEFAULT_BOILERPLATE_PATTERNS)
        assert "subscribe" not in cleaned.lower()
        assert "More content here" in cleaned

    def test_removes_cookie_notice(self):
        text = "Important data. We use cookies to improve your experience. See more."
        cleaned = _remove_boilerplate(text, DEFAULT_BOILERPLATE_PATTERNS)
        assert "cookie" not in cleaned.lower()

    def test_removes_cookie_policy(self):
        text = "Analysis follows. Cookie policy applies to all users. The results show."
        cleaned = _remove_boilerplate(text, DEFAULT_BOILERPLATE_PATTERNS)
        assert "cookie policy" not in cleaned.lower()

    def test_preserves_content(self):
        text = "The squeeze theorem is a fundamental result in calculus."
        cleaned = _remove_boilerplate(text, DEFAULT_BOILERPLATE_PATTERNS)
        assert cleaned == text


# ===================================================================
# test_language_detection
# ===================================================================

class TestLanguageDetection:
    """Stage 3: Language detection and filtering."""

    def test_english_detected(self):
        lang = _detect_language(WELL_WRITTEN_ARTICLE)
        assert lang == "en"

    def test_french_detected(self):
        lang = _detect_language(FRENCH_TEXT)
        assert lang == "fr"

    def test_english_not_skipped(self):
        result = preprocess(WELL_WRITTEN_ARTICLE, content_type="text")
        assert not result.skip
        assert result.language == "en"

    def test_french_skipped(self):
        result = preprocess(FRENCH_TEXT, content_type="text")
        assert result.skip
        assert result.skip_reason == "non_english"
        assert result.language == "fr"


# ===================================================================
# test_length_normalization
# ===================================================================

class TestLengthNormalization:
    """Stage 4: Short content is skipped; long content is smart-truncated."""

    def test_too_short_skipped(self):
        short = "A" * 100
        result = preprocess(short, content_type="text")
        assert result.skip is True
        assert result.skip_reason == "too_short"

    def test_long_text_truncated(self):
        # Build a very long text (> 10000 chars) made of real sentences
        sentence = "The squeeze theorem bounds f between g and h. "
        long_text = sentence * 500  # ~24000 chars
        assert len(long_text) > 10000

        cfg = PreprocessConfig(max_length=10000)
        text, reason = _normalise_length(long_text, cfg.min_length, cfg.max_length)
        assert reason is None
        assert len(text) <= 10100  # allow small overshoot from sentence boundary

    def test_truncation_at_sentence_boundary(self):
        # Build text with clear sentence boundaries
        sentences = [f"Sentence number {i} has some words." for i in range(300)]
        long_text = " ".join(sentences)
        cfg = PreprocessConfig(max_length=10000)
        text, reason = _normalise_length(long_text, cfg.min_length, cfg.max_length)
        assert reason is None
        # Should end with a period (sentence boundary)
        assert text.rstrip().endswith(".")


# ===================================================================
# test_quality_scoring
# ===================================================================

class TestQualityScoring:
    """Stage 5: Quality heuristics score content appropriately."""

    def test_well_written_high_quality(self):
        score = _compute_quality_score(WELL_WRITTEN_ARTICLE)
        assert score > 0.6, f"Expected > 0.6, got {score:.3f}"

    def test_repetitive_spam_low_quality(self):
        score = _compute_quality_score(REPETITIVE_SPAM)
        assert score < 0.3, f"Expected < 0.3, got {score:.3f}"

    def test_empty_string(self):
        assert _compute_quality_score("") == 0.0

    def test_single_sentence(self):
        score = _compute_quality_score("One sentence only")
        # Low variance, no paragraphs → low score
        assert score < 0.5


# ===================================================================
# test_full_pipeline
# ===================================================================

class TestFullPipeline:
    """End-to-end: HTML article through all stages."""

    def test_html_article_produces_clean_text(self):
        result = preprocess(SAMPLE_HTML, content_type="html")
        assert not result.skip, f"Unexpected skip: {result.skip_reason}"
        assert result.text is not None
        assert "squeeze theorem" in result.text.lower()
        assert result.language == "en"
        assert result.quality_score > 0.0
        assert result.processed_length > 0
        assert result.original_length == len(SAMPLE_HTML)

    def test_plain_text_article(self):
        result = preprocess(WELL_WRITTEN_ARTICLE, content_type="text")
        assert not result.skip, f"Unexpected skip: {result.skip_reason}"
        assert result.text is not None
        assert result.quality_score > 0.5

    def test_too_short_rejected(self):
        result = preprocess("Hello world.", content_type="text")
        assert result.skip
        assert result.skip_reason == "too_short"
        assert result.text is None

    def test_non_english_rejected(self):
        result = preprocess(FRENCH_TEXT, content_type="text")
        assert result.skip
        assert result.skip_reason == "non_english"

    def test_custom_config(self):
        cfg = PreprocessConfig(min_length=10, quality_threshold=0.0)
        result = preprocess("Short but ok.", content_type="text", config=cfg)
        assert not result.skip
