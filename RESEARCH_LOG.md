# SANDWICH Research Log

Observations, decisions, and findings during development and early runs.

---

## 2026-02-02: The Abstraction Problem

**Observation:** Reuben's first corpus (3 sandwiches) revealed a systematic bias toward vague, abstract ingredients. Examples:

| Sandwich | Bread Top | Filling | Bread Bottom | Validity |
|----------|-----------|---------|-------------|----------|
| The Janine Special | "Nature as source" | "Biomimetic innovation process" | "Human problems as destination" | 0.94 |
| The Continuity Club | "Medieval craft traditions" | "Organizational continuity" | "Modern professional associations" | 0.83 |
| The Scale Bridge | "Large-scale phenomena (seismic waves, earthquake mitigation)" | "Acoustic metamaterials as unified engineering approach" | "Small-scale phenomena (phonon behavior in crystals)" | 0.77 |

**Problem:** The sandwiches *sound* impressive because the LLM writes eloquently, but the actual structural content is often vague or tautological:
- "Nature as source" could describe all of applied science
- "Organizational continuity" is just restating the relationship between the bread
- "Large-scale phenomena" and "Small-scale phenomena" are literally just "big things" and "small things"

The validator scored these highly because it was evaluating the *quality of the argument* for containment, not the *specificity of the ingredients themselves*. An eloquent justification masked vague content.

**Root cause analysis:**
1. **Wikipedia summaries are too broad.** Article summaries give high-level overviews, pushing the LLM toward generalization rather than specific mechanisms.
2. **LLMs default to abstraction.** When asked to "find structure," LLMs gravitate toward the most general framing possible because abstract claims are easier to defend.
3. **No specificity penalty.** The validator had no mechanism to distinguish "gecko setae adhesion" (specific) from "nature" (could mean anything).

**Fix applied:**
1. Added explicit specificity guidance to `identifier.txt` with BAD/GOOD examples showing the difference between vague and concrete ingredients
2. Updated `assembler.txt` to resist drift from specific to abstract during construction
3. Added `specificity_score` (0.0-1.0) as a new LLM-judged validation dimension in `validator.txt`
4. Rebalanced validation weights: bread_compat=0.20, containment=0.25, specificity=0.20, nontrivial=0.15, novelty=0.20

**Hypothesis:** With specificity pressure, Reuben should produce sandwiches with more concrete, domain-specific ingredients. The overall validity scores may drop initially (the easy abstract sandwiches will score lower), but the corpus quality should improve.

**Research significance:** This is a finding worth documenting for the paper. It demonstrates that:
- LLMs systematically prefer abstraction when discovering structure
- Structural validity and content specificity are orthogonal dimensions
- Explicit specificity constraints are needed to produce meaningful knowledge artifacts
- Eloquent justification can mask vague content (a form of "bullshitting" in the Frankfurt sense)

**Next steps:**
- Run Reuben with specificity scoring and compare corpus quality
- Track whether specificity scores improve over time or plateau
- Consider whether source material quality (Wikipedia summaries vs. full articles vs. arXiv) affects specificity
- Investigate whether longer source content naturally produces more specific sandwiches

---

## 2026-02-02: Wikipedia Integration Issues

**Observation:** First run attempts failed with 403 Forbidden from Wikipedia API.

**Cause:** Wikipedia requires a descriptive User-Agent header with a URL. The original header was too generic.

**Fix:** Updated User-Agent to `"SANDWICH-Bot/1.0 (https://github.com/MLenaBleile/reuben; sandwich research project)"` and added query truncation for queries >100 characters.

**Additional issue:** The curiosity prompt was generating full sentences like "I'm curious about the relationship between quantum entanglement and classical information theory" which Wikipedia's search API handled poorly. Changed to short 2-5 word keyword queries.

---

## 2026-02-02: Prompt Templates Not Being Used

**Observation:** Despite having detailed prompt templates in `prompts/`, the LLM methods in `anthropic.py` were using hardcoded mini-prompts.

**Impact:** The identifier was using a generic prompt ("Identify potential sandwich ingredients. Respond as JSON.") instead of the full template with structure definitions, JSON format specifications, and candidate ranking instructions. This caused 0 candidates to be identified from valid content.

**Fix:** Added `_load_prompt()` helper and rewrote all LLM methods to use template files. This was a critical integration bug — the prompts were designed carefully but never wired in.

---

## 2026-02-02: pgvector Deserialization Bug

**Observation:** Second run crashed with `TypeError: can't multiply sequence by non-int of type 'float'` in the validator's cosine similarity function.

**Cause:** psycopg2 returns pgvector `vector` columns as strings like `"[0.01,0.02,...]"`. The repository's `get_sandwich_embeddings()` was calling `list(row[0])` on this string, producing a list of individual characters instead of floats.

**Fix:** Cast to `::text` in the SQL query and parse with `[float(x) for x in row[0].strip("[]").split(",")]`. This only affected corpus loading from DB — fresh embeddings computed in-memory were fine.

---
