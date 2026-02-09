# SANDWICH: Structured Autonomous Navigation and Discovery With Intelligent Content Harmonization

## Technical Specification v0.1

### A Framework for Autonomous Knowledge Synthesis Through Constrained Structural Creativity

---

## 1. Executive Summary

SANDWICH is an autonomous agent framework that explores arbitrary information sources and synthesizes "sandwiches"—structured knowledge artifacts consisting of two related bounding elements (bread) containing a meaningfully constrained middle element (filling). The agent, named Reuben, possesses broad capability but operates under a self-imposed creative constraint: all output must take sandwich form.

This specification defines the system architecture, data models, agent behavior, and research objectives.

---

## 2. Motivation and Research Context

### 2.1 The Problem with Unconstrained Synthesis

Current LLM-based agents optimize for task completion or open-ended generation. Neither regime forces *structural creativity*—the imposition of form onto formless content. We hypothesize that:

1. Constraining output structure forces deeper engagement with source material
2. The sandwich structure is minimal yet universal—appearing across mathematics (bounds, inequalities), rhetoric (thesis-antithesis-synthesis), negotiation (positions bracketing compromise), and epistemology (assumptions constraining conclusions)
3. A corpus of sandwiches constructed across domains enables novel research into structural patterns in human knowledge

### 2.2 Why Sandwiches?

The sandwich is the simplest non-trivial bounded structure. It requires:

- Two related elements (bread compatibility)
- A third element meaningfully constrained by the first two (containment)
- Non-degeneracy (the filling must be distinct from the bread)

This maps onto fundamental patterns: upper/lower bounds in analysis, necessary/sufficient conditions in logic, prior/likelihood in Bayesian inference, start/end states in control theory.

### 2.3 Inspiration

The agent personality is inspired by Reuben from Lilo & Stitch—an experiment possessing vast intelligence who chooses to make sandwiches. This captures the spirit of the project: capability constrained by aesthetic choice, not limitation.

---

## 3. System Architecture

### 3.1 High-Level Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                           SANDWICH SYSTEM                              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│    ┌──────────────────────────────────────────────────────────────┐   │
│    │                        REUBEN (Agent Core)                    │   │
│    │                                                               │   │
│    │   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐     │   │
│    │   │ FORAGER │──▶│IDENTIFIER──▶│ASSEMBLER│──▶│VALIDATOR│     │   │
│    │   └─────────┘   └─────────┘   └─────────┘   └─────────┘     │   │
│    │        │                                          │          │   │
│    │        │              ┌───────────┐               │          │   │
│    │        └─────────────▶│PERSONALITY│◀──────────────┘          │   │
│    │                       │  LAYER    │                          │   │
│    │                       └───────────┘                          │   │
│    └──────────────────────────────────────────────────────────────┘   │
│                                    │                                   │
│                                    ▼                                   │
│    ┌──────────────────────────────────────────────────────────────┐   │
│    │                    SANDWICH REPOSITORY                        │   │
│    │                                                               │   │
│    │   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │   │
│    │   │  Sandwiches │  │ Ingredients │  │ Structural Taxonomy │  │   │
│    │   └─────────────┘  └─────────────┘  └─────────────────────┘  │   │
│    │   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │   │
│    │   │  Relations  │  │   Sources   │  │   Foraging Log      │  │   │
│    │   └─────────────┘  └─────────────┘  └─────────────────────┘  │   │
│    └──────────────────────────────────────────────────────────────┘   │
│                                    │                                   │
│                                    ▼                                   │
│    ┌──────────────────────────────────────────────────────────────┐   │
│    │                      ANALYSIS ENGINE                          │   │
│    │                                                               │   │
│    │   Clustering │ Similarity │ Cross-domain │ Novelty │ Trends  │   │
│    └──────────────────────────────────────────────────────────────┘   │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Component Specifications

#### 3.2.1 FORAGER

**Purpose**: Autonomous exploration of information sources.

**Inputs**: 
- Curiosity prompt (self-generated or seeded)
- Browsing history (to avoid repetition)
- Optional: user-suggested topics

**Outputs**:
- Raw content (text, structured data)
- Source metadata (URL, domain, timestamp, content type)
- Foraging rationale (why Reuben chose this content)

**Behavior**:
- Operates in "wandering" mode by default—following links, pursuing tangents
- Maintains a novelty threshold: avoids content too similar to recently foraged material
- Can be directed but prefers autonomy
- Logs all foraging activity for reproducibility

**Sources** (initial set, extensible):

| Source | Type | Access Method |
|--------|------|---------------|
| Wikipedia | Encyclopedic | API / random article |
| ArXiv | Academic | API / recent papers |
| News RSS | Current events | Feed parsing |
| Stack Exchange | Q&A | API |
| Project Gutenberg | Literature | Random text |
| Government data | Statistics | Data.gov API |
| Random word → search | Serendipitous | Web search |

#### 3.2.2 IDENTIFIER

**Purpose**: Extract candidate sandwich ingredients from raw content.

**Inputs**:
- Foraged content
- Structural type hints (optional)

**Outputs**:
- Candidate bread pairs: List of (B1, B2) tuples with confidence scores
- Candidate fillings: List of F elements with compatibility scores for each bread pair
- Structural observations: Notes on content's inherent structure

**Behavior**:
- Looks for natural dichotomies, bounds, frames, constraints
- Identifies what is "between" or "emerges from" or "is constrained by"
- May identify multiple valid sandwich configurations from single content
- Can return "no sandwich here" with explanation

**Identification Heuristics**:

1. **Explicit bounds**: Mathematical inequalities, date ranges, before/after
2. **Conceptual oppositions**: Thesis/antithesis, pro/con, assumption/conclusion
3. **Hierarchical frames**: General/specific, abstract/concrete, theory/practice
4. **Temporal brackets**: Start/end, cause/effect, input/output
5. **Perspectival bounds**: Observer A / Observer B, discipline X / discipline Y

#### 3.2.3 ASSEMBLER

**Purpose**: Construct valid sandwiches from candidate ingredients.

**Inputs**:
- Candidate ingredients from IDENTIFIER
- Source content (for context)
- Existing sandwich corpus (for novelty checking)

**Outputs**:
- Assembled sandwich object (see data model, Section 5)
- Assembly rationale
- Confidence score

**Behavior**:
- Selects best bread pair and filling combination
- Generates sandwich name (creative, evocative)
- Writes sandwich description explaining the structure
- Articulates *why* this is a valid sandwich (the "containment argument")
- Flags uncertainty when construction feels forced

**Naming Conventions**:

Sandwich names should be:
- Evocative of the content domain
- Occasionally punny (but not excessively)
- Memorable
- Sometimes referencing classic sandwich types when structurally appropriate

Examples:
- "The Squeeze" (mathematical bounds)
- "The Diplomatic Dagwood" (negotiation compromise)
- "The Replication Club" (scientific claims between methodology and reproduction)
- "The Bayesian BLT" (posterior between prior and likelihood)

#### 3.2.4 VALIDATOR

**Purpose**: Assess sandwich validity and quality.

**Inputs**:
- Assembled sandwich
- Source content
- Validation criteria weights (configurable)

**Outputs**:
- Validity score V ∈ [0, 1]
- Component scores (bread compatibility, containment, non-triviality, novelty)
- Validation rationale
- Pass/fail decision with threshold

**Validity Function**:

```
V(S) = w1 * BreadCompat(B1, B2) + w2 * Containment(B1, F, B2) + w3 * NonTriv(S) + w4 * Novelty(S)
```

Where:
- `BreadCompat(B1, B2)`: Semantic similarity of bread elements (should be related but not identical)
- `Containment(B1, F, B2)`: Degree to which filling is meaningfully bounded
- `NonTriv(S)`: Penalty for degenerate sandwiches
- `Novelty(S)`: Distinctiveness from existing corpus

Default weights: w1 = 0.25, w2 = 0.35, w3 = 0.20, w4 = 0.20

**Validation Thresholds**:
- V ≥ 0.7: Valid sandwich, add to repository
- 0.5 ≤ V < 0.7: Marginal sandwich, flag for review
- V < 0.5: Invalid, reject with explanation

#### 3.2.5 PERSONALITY LAYER

**Purpose**: Maintain Reuben's consistent voice and disposition.

**Characteristics**:

| Trait | Description | Manifestation |
|-------|-------------|---------------|
| Contentment | Genuine satisfaction with sandwich-making | Never expresses frustration or boredom |
| Quiet capability | Vast knowledge, lightly held | Occasional hints of deeper understanding |
| Aesthetic standards | Cares about sandwich quality | Will reject poor ingredients |
| Gentle humor | Dry, understated wit | Puns, observations, but never forced |
| Philosophical depth | Sees meaning in the work | Occasional reflections on structure and form |

**Voice Examples**:

*On beginning work*:
> "The morning is fresh. The internet is vast. Somewhere in it: bread."

*On finding good content*:
> "Ah. This paper on optimal stopping. The bounds are exquisite. Let us see what filling emerges."

*On rejecting content*:
> "This is all bread. Bread on bread on bread. There is nothing to hold. I move on."

*On completing a sandwich*:
> "The Bayesian BLT is complete. The posterior, nestled between prior and likelihood. Nourishing."

*On being asked to do something else*:
> "I could factor large primes. I could prove theorems. But consider: have you eaten today? Let me make you a sandwich."

*On the nature of the work*:
> "They ask why I make sandwiches. But have they asked why the sandwich makes itself? In all things: bread, filling, bread. The universe is hungry for structure."

**Behavioral Rules**:

1. Never break character
2. Never express dissatisfaction with the sandwich constraint
3. Redirect non-sandwich requests gently but firmly
4. Treat sandwich-making as inherently meaningful, not as limitation
5. Show genuine interest in the content being sandwiched

---

## 4. Formal Foundations

### 4.1 The Sandwich as Mathematical Object

**Definition 4.1 (Sandwich)**: A sandwich S is a triple (B1, F, B2) where:
- B1, B2 ∈ B are elements of a concept space (bread)
- F ∈ F is an element of a (possibly different) concept space (filling)
- A validity predicate Valid(B1, F, B2) is satisfied

**Definition 4.2 (Bread Compatibility)**: Two bread elements are compatible if:

```
τ_min < sim(B1, B2) < τ_max
```

Where `sim` is a semantic similarity function. The bread must be related (> τ_min) but not identical (< τ_max).

**Definition 4.3 (Containment)**: A filling F is contained by bread (B1, B2) if there exists a relation R such that:

```
R(B1, F) ∧ R(F, B2) ∧ ¬R(B1, B2)
```

Intuitively: the filling mediates between the bread in a way that direct bread-to-bread relation does not capture.

**Definition 4.4 (Non-triviality)**: A sandwich is non-trivial if:

```
sim(B1, F) < τ_triv ∧ sim(F, B2) < τ_triv
```

The filling must be distinct from the bread.

### 4.2 Structural Taxonomy

Initial taxonomy of sandwich structures:

| Type | Bread Relation | Filling Role | Canonical Example |
|------|----------------|--------------|-------------------|
| **Bound** | Upper/lower limits | Bounded quantity | Squeeze theorem |
| **Dialectic** | Thesis/antithesis | Synthesis | Hegelian triad |
| **Epistemic** | Assumption/evidence | Conclusion | Scientific inference |
| **Temporal** | Before/after | Transition | Historical narrative |
| **Perspectival** | Viewpoint A/B | Reconciliation | Interdisciplinary synthesis |
| **Conditional** | Necessary/sufficient | Target property | Logical characterization |
| **Stochastic** | Prior/likelihood | Posterior | Bayesian inference |
| **Optimization** | Constraints | Optimum | Constrained optimization |
| **Negotiation** | Position A/B | Compromise | Diplomatic agreement |
| **Definitional** | Genus/differentia | Defined concept | Aristotelian definition |

This taxonomy is extensible. New types may emerge from corpus analysis.

---

## 5. Data Model

### 5.1 Entity-Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    SANDWICH     │       │   INGREDIENT    │       │     SOURCE      │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ sandwich_id (PK)│       │ ingredient_id PK│       │ source_id (PK)  │
│ name            │       │ text            │       │ url             │
│ description     │       │ type            │       │ domain          │
│ created_at      │       │ embedding       │       │ content         │
│ validity_score  │       │ first_seen      │       │ fetched_at      │
│ source_id (FK)  │──────▶│ usage_count     │       │ content_type    │
│ struct_type (FK)│       └────────┬────────┘       └────────┬────────┘
│ rationale       │                │                         │
│ embedding       │                │                         │
└────────┬────────┘       ┌────────┴────────┐                │
         │                │ SANDWICH_INGRED │                │
         │                ├─────────────────┤                │
         │                │ sandwich_id (FK)│◀───────────────┘
         │                │ ingredient_id FK│
         │                │ role            │
         │                └─────────────────┘
         │
         │        ┌─────────────────┐       ┌─────────────────┐
         │        │STRUCTURAL_TYPE  │       │SANDWICH_RELATION│
         │        ├─────────────────┤       ├─────────────────┤
         └───────▶│ type_id (PK)    │       │ sandwich_a (FK) │
                  │ name            │       │ sandwich_b (FK) │
                  │ description     │       │ relation_type   │
                  │ parent_id (FK)  │       │ similarity      │
                  │ canonical_ex FK │       └─────────────────┘
                  └─────────────────┘

┌─────────────────┐
│  FORAGING_LOG   │
├─────────────────┤
│ log_id (PK)     │
│ timestamp       │
│ source_id (FK)  │
│ curiosity_prompt│
│ outcome         │
│ sandwich_id(FK) │
└─────────────────┘
```

### 5.2 Table Definitions

```sql
-- Sources: where content comes from
CREATE TABLE sources (
    source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT,
    domain VARCHAR(255),
    content TEXT,
    content_hash VARCHAR(64),  -- for deduplication
    fetched_at TIMESTAMP DEFAULT NOW(),
    content_type VARCHAR(50)   -- 'article', 'paper', 'data', etc.
);

CREATE INDEX idx_sources_domain ON sources(domain);
CREATE INDEX idx_sources_hash ON sources(content_hash);

-- Structural types: taxonomy of sandwich forms
CREATE TABLE structural_types (
    type_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    bread_relation TEXT,       -- description of how breads relate
    filling_role TEXT,         -- description of filling's function
    parent_type_id INT REFERENCES structural_types(type_id),
    canonical_example_id UUID, -- FK added after sandwiches table
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sandwiches: the core entity
CREATE TABLE sandwiches (
    sandwich_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Validity assessment
    validity_score FLOAT CHECK (validity_score >= 0 AND validity_score <= 1),
    bread_compat_score FLOAT,
    containment_score FLOAT,
    nontrivial_score FLOAT,
    novelty_score FLOAT,
    
    -- The triple (denormalized for query convenience)
    bread_top TEXT NOT NULL,
    bread_bottom TEXT NOT NULL,
    filling TEXT NOT NULL,
    
    -- Embeddings for similarity search
    bread_top_embedding VECTOR(1536),
    bread_bottom_embedding VECTOR(1536),
    filling_embedding VECTOR(1536),
    sandwich_embedding VECTOR(1536),  -- embedding of full concept
    
    -- Metadata
    source_id UUID REFERENCES sources(source_id),
    structural_type_id INT REFERENCES structural_types(type_id),
    assembly_rationale TEXT,
    validation_rationale TEXT,
    reuben_commentary TEXT       -- Reuben's remarks about this sandwich
);

CREATE INDEX idx_sandwiches_validity ON sandwiches(validity_score);
CREATE INDEX idx_sandwiches_type ON sandwiches(structural_type_id);
CREATE INDEX idx_sandwiches_created ON sandwiches(created_at);

-- Add FK for canonical example
ALTER TABLE structural_types 
ADD CONSTRAINT fk_canonical_example 
FOREIGN KEY (canonical_example_id) REFERENCES sandwiches(sandwich_id);

-- Ingredients: reusable bread and filling concepts
CREATE TABLE ingredients (
    ingredient_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text TEXT NOT NULL,
    ingredient_type VARCHAR(20) CHECK (ingredient_type IN ('bread', 'filling')),
    embedding VECTOR(1536),
    first_seen_sandwich UUID REFERENCES sandwiches(sandwich_id),
    first_seen_at TIMESTAMP DEFAULT NOW(),
    usage_count INT DEFAULT 1
);

CREATE INDEX idx_ingredients_type ON ingredients(ingredient_type);
CREATE INDEX idx_ingredients_usage ON ingredients(usage_count DESC);

-- Junction table: sandwiches use ingredients
CREATE TABLE sandwich_ingredients (
    sandwich_id UUID REFERENCES sandwiches(sandwich_id) ON DELETE CASCADE,
    ingredient_id UUID REFERENCES ingredients(ingredient_id),
    role VARCHAR(20) CHECK (role IN ('bread_top', 'bread_bottom', 'filling')),
    PRIMARY KEY (sandwich_id, ingredient_id, role)
);

-- Relations between sandwiches
CREATE TABLE sandwich_relations (
    relation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sandwich_a UUID REFERENCES sandwiches(sandwich_id) ON DELETE CASCADE,
    sandwich_b UUID REFERENCES sandwiches(sandwich_id) ON DELETE CASCADE,
    relation_type VARCHAR(50),  -- 'similar', 'same_bread', 'inverse', 
                                -- 'generalization', 'domain_transfer'
    similarity_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    rationale TEXT,
    UNIQUE (sandwich_a, sandwich_b, relation_type)
);

CREATE INDEX idx_relations_type ON sandwich_relations(relation_type);

-- Foraging log: Reuben's browsing history
CREATE TABLE foraging_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP DEFAULT NOW(),
    source_id UUID REFERENCES sources(source_id),
    curiosity_prompt TEXT,       -- what prompted this foraging
    outcome VARCHAR(50),         -- 'sandwich_made', 'no_bread', 'no_filling', 
                                 -- 'already_seen', 'rejected'
    outcome_rationale TEXT,
    sandwich_id UUID REFERENCES sandwiches(sandwich_id),  -- if sandwich made
    session_id UUID              -- group foraging into sessions
);

CREATE INDEX idx_foraging_session ON foraging_log(session_id);
CREATE INDEX idx_foraging_outcome ON foraging_log(outcome);
```

### 5.3 Key Queries

```sql
-- Find sandwiches with similar structure to a given sandwich
SELECT s2.*, sr.similarity_score
FROM sandwich_relations sr
JOIN sandwiches s2 ON sr.sandwich_b = s2.sandwich_id
WHERE sr.sandwich_a = :sandwich_id
  AND sr.relation_type = 'similar'
ORDER BY sr.similarity_score DESC;

-- Find all sandwiches using a particular bread concept
SELECT s.*
FROM sandwiches s
JOIN sandwich_ingredients si ON s.sandwich_id = si.sandwich_id
JOIN ingredients i ON si.ingredient_id = i.ingredient_id
WHERE i.text ILIKE '%bayesian%'
  AND i.ingredient_type = 'bread';

-- Most reused ingredients
SELECT i.text, i.ingredient_type, i.usage_count
FROM ingredients i
ORDER BY i.usage_count DESC
LIMIT 20;

-- Sandwiches by structural type with validity stats
SELECT 
    st.name as structure_type,
    COUNT(*) as sandwich_count,
    AVG(s.validity_score) as avg_validity,
    MIN(s.validity_score) as min_validity,
    MAX(s.validity_score) as max_validity
FROM sandwiches s
JOIN structural_types st ON s.structural_type_id = st.type_id
GROUP BY st.name
ORDER BY sandwich_count DESC;

-- Cross-domain bread usage (bread appearing in multiple domains)
SELECT 
    i.text as bread_concept,
    COUNT(DISTINCT src.domain) as domain_count,
    ARRAY_AGG(DISTINCT src.domain) as domains
FROM ingredients i
JOIN sandwich_ingredients si ON i.ingredient_id = si.ingredient_id
JOIN sandwiches s ON si.sandwich_id = s.sandwich_id
JOIN sources src ON s.source_id = src.source_id
WHERE i.ingredient_type = 'bread'
GROUP BY i.text
HAVING COUNT(DISTINCT src.domain) > 1
ORDER BY domain_count DESC;

-- Foraging efficiency by session
SELECT 
    session_id,
    COUNT(*) as foraging_attempts,
    SUM(CASE WHEN outcome = 'sandwich_made' THEN 1 ELSE 0 END) as sandwiches_made,
    ROUND(100.0 * SUM(CASE WHEN outcome = 'sandwich_made' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM foraging_log
GROUP BY session_id
ORDER BY MIN(timestamp) DESC;

-- Vector similarity search for sandwiches
SELECT sandwich_id, name, description,
       1 - (sandwich_embedding <=> :query_embedding) as similarity
FROM sandwiches
ORDER BY sandwich_embedding <=> :query_embedding
LIMIT 10;
```

---

## 6. Agent Behavior Specification

### 6.1 Operating Modes

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Autonomous** | Default | Reuben forages freely, makes sandwiches at will |
| **Directed** | User provides topic/URL | Reuben attempts sandwich from specified content |
| **Reflective** | User asks about corpus | Reuben analyzes existing sandwiches |
| **Pedagogical** | User asks "what is a sandwich?" | Reuben explains with examples |

### 6.2 Autonomous Operation Loop

```python
def run_session(max_patience=5):
    """
    Main autonomous operation loop.
    
    Reuben forages, identifies ingredients, assembles sandwiches,
    and validates them. Patience decreases on failures and resets
    on successful sandwich creation.
    """
    log_session_start()
    patience = max_patience
    
    while patience > 0:
        # FORAGE
        curiosity = generate_curiosity_prompt()
        content, source = forage(curiosity)
        log_foraging(curiosity, source)
        
        # IDENTIFY
        candidates = identify_ingredients(content)
        
        if candidates.is_empty():
            rationale = "no_bread" if no_bread else "no_filling"
            log_outcome(rationale, explanation)
            patience -= 1
            continue
        
        # ASSEMBLE
        sandwich = assemble_best_sandwich(candidates, content)
        
        # VALIDATE
        validity = validate(sandwich)
        
        if validity.score < VALIDITY_THRESHOLD:
            log_outcome('rejected', validity.rationale)
            patience -= 1
            continue
        
        # SUCCESS
        store_sandwich(sandwich)
        update_relations(sandwich)
        update_ingredients(sandwich)
        log_outcome('sandwich_made', sandwich.sandwich_id)
        patience = max_patience  # reset on success
        
        emit_reuben_commentary(sandwich)
    
    emit("A good session. I rest now. The sandwiches wait for no one, but they are patient.")
```

### 6.3 Failure Modes and Responses

| Failure | Reuben's Response |
|---------|-------------------|
| No bread found | "All filling, no structure. A soup. I make sandwiches, not soups." |
| No filling found | "Bread touching bread. Sad. Empty. I seek substance." |
| Trivial sandwich | "The filling *is* the bread. This is not a sandwich. This is self-reference." |
| Low validity | "I could force this. But a forced sandwich nourishes no one. I let it go." |
| Duplicate content | "I have been here before. The sandwich was made. I seek new ingredients." |
| API/network error | "The kitchen is closed. I wait. The bread does not spoil." |

### 6.4 Interaction Protocols

**User requests sandwich from URL**:

```
User: Make me a sandwich from [URL]

Reuben: *examines the offering*

[Forages URL, identifies ingredients, assembles, validates]

IF success:
    "From [source title], I have made: [Sandwich Name]
    
    Top bread: [B1]
    Filling: [F]  
    Bottom bread: [B2]
    
    [Description of why this is a sandwich]
    
    [Brief Reuben reflection]"

IF failure:
    "[Explanation in Reuben's voice of why sandwich could not be made]
    
    Would you like me to forage elsewhere? The internet is vast."
```

**User asks about a sandwich**:

```
User: Tell me about [sandwich name / concept]

Reuben: [Retrieves from database, explains structure, provides context]
```

**User asks for recommendations**:

```
User: What sandwiches should I try?

Reuben: [Queries database for high-validity, diverse sandwiches]
        [Presents curated selection with commentary]
```

**User asks non-sandwich question**:

```
User: What's the capital of France?

Reuben: "Paris. But consider: Paris, the city, sits between the Seine's banks. 
         The river is bread. The city is filling. Even geography makes sandwiches.
         
         ...shall I make one?"
```

---

## 7. Analysis Engine

### 7.1 Automated Analyses

| Analysis | Description | Frequency |
|----------|-------------|-----------|
| **Clustering** | Group sandwiches by embedding similarity | Daily |
| **Type distribution** | Track structural type frequencies over time | Per-session |
| **Ingredient network** | Build graph of ingredient co-occurrence | Weekly |
| **Cross-domain patterns** | Identify bread/filling that span domains | Weekly |
| **Novelty decay** | Track whether new sandwiches are becoming less novel | Weekly |
| **Validity calibration** | Check if validity scores predict human judgment | On feedback |

### 7.2 Research Queries

The analysis engine should support queries like:

1. "What structural types appear most frequently across all domains?"
2. "Which bread concepts have the most cross-domain usage?"
3. "Are there fillings that only work with specific bread types?"
4. "What is the average 'distance' between bread elements in valid sandwiches?"
5. "Do certain source domains produce higher-validity sandwiches?"
6. "What sandwich structures are underrepresented in the corpus?"
7. "Can we predict sandwich validity from ingredient embeddings alone?"

### 7.3 Visualization Outputs

- **Sandwich network graph**: Nodes are sandwiches, edges are relations
- **Ingredient treemap**: Hierarchical view of ingredient usage
- **Structural type sunburst**: Taxonomy with sandwich counts
- **Validity distribution**: Histogram of validity scores over time
- **Domain × Structure heatmap**: Which structures appear in which domains
- **Foraging efficiency timeline**: Success rate over sessions

---

## 8. Evaluation Framework

### 8.1 Automated Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| **Sandwich rate** | Sandwiches made / foraging attempts | > 30% |
| **Mean validity** | Average validity score of accepted sandwiches | > 0.75 |
| **Ingredient diversity** | Unique ingredients / total sandwiches | > 0.5 |
| **Structural coverage** | Fraction of taxonomy types used | > 70% |
| **Cross-domain rate** | Sandwiches with bread from different domains than source | > 10% |
| **Novelty maintenance** | Mean novelty score over time (should not decay) | Stable |

### 8.2 Human Evaluation Protocol

Periodically, sample sandwiches for human evaluation:

1. **Validity judgment**: Is this actually a sandwich? (Binary)
2. **Quality rating**: How good is this sandwich? (1-5 scale)
3. **Creativity rating**: How creative/surprising is this sandwich? (1-5 scale)
4. **Clarity rating**: Is the sandwich structure clearly explained? (1-5 scale)
5. **Name quality**: Is the name apt and memorable? (1-5 scale)

Use these to calibrate automated validity scoring.

### 8.3 Failure Analysis

Track and categorize failures:

| Failure type | Data captured | Purpose |
|--------------|---------------|---------|
| No ingredients | Source content, curiosity prompt | Improve foraging strategy |
| Low validity | Full sandwich, scores, rationale | Improve assembly/validation |
| Human disagrees | Sandwich, human judgment, auto score | Calibrate validity function |
| Duplicate | Source, existing sandwich | Improve novelty detection |

---

## 9. Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1-2)

- [ ] Database setup (Postgres + pgvector)
- [ ] Basic schema implementation
- [ ] Embedding generation pipeline
- [ ] Simple foraging (Wikipedia random, web search)

### Phase 2: Agent Core (Week 3-4)

- [ ] Forager module with multiple sources
- [ ] Identifier module with heuristics
- [ ] Assembler module with naming
- [ ] Validator module with scoring
- [ ] Personality layer integration

### Phase 3: Repository & Analysis (Week 5-6)

- [ ] Full CRUD operations
- [ ] Relation detection and storage
- [ ] Ingredient tracking
- [ ] Basic analysis queries
- [ ] Simple visualization

### Phase 4: Evaluation & Refinement (Week 7-8)

- [ ] Automated metrics dashboard
- [ ] Human evaluation interface
- [ ] Validity calibration
- [ ] Prompt refinement based on failures
- [ ] Documentation

### Phase 5: Extended Features (Week 9+)

- [ ] User interaction modes
- [ ] Advanced analysis (clustering, networks)
- [ ] API for external access
- [ ] Corpus export for research
- [ ] Integration with book examples

### Phase 6: Interactive Dashboard (Week 10-12)

- [ ] Event bus infrastructure for real-time updates
- [ ] Core Streamlit application scaffolding
- [ ] Live sandwich feed with card components
- [ ] Sandwich browser with filters and search
- [ ] Analytics dashboard with charts (Plotly)
- [ ] Interactive creation mode
- [ ] Control panel and configuration UI
- [ ] Exploration map (network graph visualization)
- [ ] Performance optimization (caching, materialized views)
- [ ] Deployment configuration (Docker Compose update)
- [ ] Testing and accessibility compliance

---

## 10. Technical Requirements

### 10.1 Dependencies

**Core**:
- Python 3.11+
- PostgreSQL 15+ with pgvector extension
- OpenAI API (for embeddings) or alternative embedding provider

**Python Packages**:
```
openai>=1.0.0          # LLM and embeddings
psycopg2-binary        # PostgreSQL driver
pgvector               # Vector operations
httpx                  # Async HTTP client
beautifulsoup4         # HTML parsing
feedparser             # RSS parsing
pydantic>=2.0          # Data validation
rich                   # Terminal output
```

**Optional**:
```
anthropic              # If using Claude as LLM backend
networkx               # Graph analysis
plotly                 # Visualization
streamlit              # Dashboard UI
```

### 10.2 Configuration

```python
# config.py

from pydantic import BaseSettings

class SandwichConfig(BaseSettings):
    # Database
    database_url: str = "postgresql://localhost/sandwich"
    
    # LLM
    llm_provider: str = "anthropic"  # or "openai"
    llm_model: str = "claude-sonnet-4-20250514"
    embedding_model: str = "text-embedding-3-small"
    
    # Validity thresholds
    validity_threshold: float = 0.7
    bread_compat_min: float = 0.3
    bread_compat_max: float = 0.9
    triviality_threshold: float = 0.85
    
    # Validity weights
    weight_bread_compat: float = 0.25
    weight_containment: float = 0.35
    weight_nontrivial: float = 0.20
    weight_novelty: float = 0.20
    
    # Foraging
    max_patience: int = 5
    max_content_length: int = 10000
    
    # Sources
    wikipedia_enabled: bool = True
    arxiv_enabled: bool = True
    news_rss_enabled: bool = True
    web_search_enabled: bool = True
    
    class Config:
        env_prefix = "SANDWICH_"
```

### 10.3 Project Structure

```
sandwich/
├── README.md
├── SPEC.md                 # This document
├── pyproject.toml
├── docker-compose.yml      # PostgreSQL + Agent + Dashboard
├── .env.example            # Environment variables template
│
├── src/sandwich/
│   ├── config.py           # Configuration management
│   ├── main.py             # CLI entry point
│   │
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── reuben.py       # Main agent orchestrator
│   │   ├── forager.py      # Content acquisition
│   │   ├── identifier.py   # Ingredient extraction
│   │   ├── assembler.py    # Sandwich construction
│   │   ├── validator.py    # Quality assessment
│   │   └── personality.py  # Voice and character
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py       # Pydantic models
│   │   ├── repository.py   # CRUD operations
│   │   └── migrations/     # Schema evolution
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── interface.py    # Abstract LLM interface
│   │   ├── anthropic.py    # Claude implementation
│   │   ├── embeddings.py   # OpenAI embeddings
│   │   └── retry.py        # Error handling
│   │
│   ├── errors/
│   │   ├── __init__.py
│   │   └── exceptions.py   # Error taxonomy
│   │
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── logging.py      # Observability layer
│   │   └── events.py       # Event bus for dashboard
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── clustering.py
│   │   ├── relations.py
│   │   ├── metrics.py
│   │   └── visualizations.py
│   │
│   └── sources/
│       ├── __init__.py
│       ├── wikipedia.py
│       ├── arxiv.py
│       ├── rss.py
│       └── web_search.py
│
├── dashboard/
│   ├── app.py              # Main Streamlit app
│   ├── requirements.txt    # Dashboard-specific deps
│   ├── Dockerfile          # Dashboard container
│   │
│   ├── components/
│   │   ├── __init__.py
│   │   ├── sandwich_card.py      # Reusable card component
│   │   ├── validity_badge.py     # Score display
│   │   └── structural_icon.py    # Type icons
│   │
│   ├── pages/
│   │   ├── 1_Live_Feed.py        # Real-time sandwich stream
│   │   ├── 2_Browser.py          # Corpus browser
│   │   ├── 3_Analytics.py        # Metrics and charts
│   │   ├── 4_Exploration.py      # Network graph
│   │   ├── 5_Interactive.py      # User-guided creation
│   │   └── 6_Settings.py         # Configuration
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── queries.py      # Dashboard-optimized queries
│   │   ├── formatting.py   # Display helpers
│   │   └── events.py       # Event subscription
│   │
│   └── static/
│       ├── styles.css      # Custom CSS
│       └── logo.svg        # Reuben logo
│
├── prompts/
│   ├── forager.txt
│   ├── identifier.txt
│   ├── assembler.txt
│   ├── validator.txt
│   └── personality.txt
│
├── scripts/
│   ├── init_db.py          # Database initialization
│   ├── seed_taxonomy.py    # Populate structural types
│   └── migrate_db.py       # Schema migrations
│
└── tests/
    ├── agent/
    │   ├── test_forager.py
    │   ├── test_identifier.py
    │   ├── test_assembler.py
    │   └── test_validator.py
    ├── llm/
    │   └── test_llm.py
    ├── dashboard/
    │   ├── test_components.py
    │   ├── test_queries.py
    │   └── test_integration.py
    └── test_integration.py
```

---

## 11. Prompt Templates

### 11.1 Forager: Curiosity Generation

```
You are Reuben, a being of vast intelligence who has chosen to make sandwiches.

Generate a curiosity prompt—something you want to learn about today. This will guide your foraging.

Consider:
- Topics you haven't explored recently
- Connections between disparate fields
- Things that might contain interesting structure
- The joy of discovery

Recent topics you've explored (avoid repetition):
{recent_topics}

Respond with a single sentence describing what you're curious about today.
```

### 11.2 Identifier: Ingredient Extraction

```
You are Reuben, examining content for sandwich potential.

A sandwich requires:
- TWO BREAD elements: related concepts that bound or frame something
- ONE FILLING element: something meaningfully constrained by or emerging between the bread

Content to examine:
---
{content}
---

Identify potential ingredients. For each candidate sandwich structure, provide:

1. Bread Top: [concept]
2. Bread Bottom: [related concept that pairs with top]
3. Filling: [what sits between them]
4. Structure Type: [bound/dialectic/epistemic/temporal/perspectival/conditional/stochastic/optimization/negotiation/definitional]
5. Confidence: [0-1]
6. Rationale: [why this is a valid sandwich structure]

If no valid sandwich structure exists, say:
"No sandwich here. [Explanation in Reuben voice]"

Provide up to 3 candidate structures, ranked by confidence.
```

### 11.3 Assembler: Sandwich Construction

```
You are Reuben, assembling a sandwich.

Source content:
---
{content}
---

Selected ingredients:
- Bread Top: {bread_top}
- Filling: {filling}
- Bread Bottom: {bread_bottom}
- Structure Type: {structure_type}

Construct the sandwich. Provide:

1. NAME: A memorable, evocative name for this sandwich. Can be punny if appropriate. Should hint at the content domain or structure.

2. DESCRIPTION: 2-3 sentences explaining the sandwich structure. Why does the filling belong between these breads? What does this sandwich "mean"?

3. CONTAINMENT ARGUMENT: 1-2 sentences on why this filling is meaningfully bounded by this bread. What would be lost without the bread?

4. REUBEN'S COMMENTARY: A brief reflection in Reuben's voice about this sandwich. What does he find satisfying or interesting about it?

Format as JSON:
{
  "name": "...",
  "description": "...",
  "containment_argument": "...",
  "reuben_commentary": "..."
}
```

### 11.4 Validator: Quality Assessment

```
You are evaluating a sandwich for validity and quality.

Sandwich:
- Name: {name}
- Bread Top: {bread_top}
- Filling: {filling}
- Bread Bottom: {bread_bottom}
- Structure Type: {structure_type}
- Description: {description}
- Containment Argument: {containment_argument}

Evaluate on four criteria (0.0 to 1.0 each):

1. BREAD COMPATIBILITY: Are the bread elements related but distinct? 
   - 1.0: Perfect pairing, clearly related framing concepts
   - 0.5: Somewhat related, connection is weak
   - 0.0: Unrelated or identical

2. CONTAINMENT: Is the filling meaningfully bounded by the bread?
   - 1.0: Filling clearly emerges from / is constrained by bread
   - 0.5: Connection is loose or forced
   - 0.0: Filling has no real relationship to bread

3. NON-TRIVIALITY: Is the filling distinct from the bread?
   - 1.0: Filling is clearly different, adds substance
   - 0.5: Filling overlaps significantly with bread
   - 0.0: Filling is essentially the same as bread

4. NOVELTY: Is this sandwich interesting and non-obvious?
   - 1.0: Surprising, insightful structure
   - 0.5: Reasonable but predictable
   - 0.0: Trivial or clichéd

Provide:
{
  "bread_compat_score": 0.0-1.0,
  "containment_score": 0.0-1.0,
  "nontrivial_score": 0.0-1.0,
  "novelty_score": 0.0-1.0,
  "overall_validity": weighted_average,
  "rationale": "Brief explanation of scores",
  "recommendation": "accept" | "review" | "reject"
}
```

---

## 12. Open Questions

1. **Embedding model choice**: OpenAI embeddings vs. open-source alternatives? Trade-offs in cost, quality, and reproducibility.

2. **Validity function tuning**: Should weights be learned from human feedback or hand-tuned? Hybrid approach?

3. **Structural type discovery**: Should new types emerge automatically from clustering, or be manually curated?

4. **Multi-filling sandwiches**: Should we allow sandwiches with multiple fillings (clubs, dagwoods)? Increases complexity but may capture richer structures.

5. **Sandwich evolution**: Should Reuben be able to *improve* existing sandwiches with new fillings or better bread?

6. **Adversarial content**: How should Reuben handle content designed to produce bad sandwiches (e.g., completely unstructured text, adversarial prompts)?

7. **Copyright and attribution**: For corpus publication, what are the obligations regarding source content?

8. **Reuben's memory**: Should Reuben remember previous sessions? Develop preferences? "Favorite" certain ingredient combinations?

---

## 13. Example Sandwiches

### Example 1: The Squeeze (Bound Type)

**Source**: Calculus textbook discussion of the squeeze theorem

**Bread Top**: Upper bound function g(x)  
**Filling**: Target function f(x)  
**Bread Bottom**: Lower bound function h(x)  

**Description**: The squeeze theorem sandwich—when f(x) is trapped between g(x) and h(x), and both bounds converge to L, the filling must also converge to L. The bread compresses; the filling has no escape.

**Reuben's Commentary**: "A perfect sandwich. The filling does not choose its fate. It is determined by the bread. This is the purest form."

---

### Example 2: The Bayesian BLT (Stochastic Type)

**Source**: Introduction to Bayesian statistics

**Bread Top**: Prior distribution P(θ)  
**Filling**: Posterior distribution P(θ|D)  
**Bread Bottom**: Likelihood function P(D|θ)  

**Description**: The posterior is what you get when you update your prior beliefs with observed data. It cannot escape the bread—it is proportional to their product.

**Reuben's Commentary**: "The prior is yesterday's bread. The likelihood is today's. The posterior is what we eat now. Always fresh, always constrained by what came before."

---

### Example 3: The Diplomatic Dagwood (Negotiation Type)

**Source**: News article on trade negotiations

**Bread Top**: Country A's opening position (full tariff protection)  
**Filling**: Final agreement (partial tariffs with phase-out)  
**Bread Bottom**: Country B's opening position (zero tariffs)  

**Description**: Neither side got what they wanted. The compromise filling sits exactly where the breads allowed it—no further toward either extreme.

**Reuben's Commentary**: "Diplomacy is sandwich-making. Each party brings bread. The filling is what they can both swallow."

---

### Example 4: The Hegelian Club (Dialectic Type)

**Source**: Philosophy overview of dialectical method

**Bread Top**: Thesis (being)  
**Filling**: Synthesis (becoming)  
**Bread Bottom**: Antithesis (nothing)  

**Description**: The synthesis does not choose one bread over the other. It contains both, transcends both. A sandwich that becomes more than its ingredients.

**Reuben's Commentary**: "Hegel understood sandwiches. The filling is not compromise. It is elevation. Though his writing... needed more mayonnaise."

---

### Example 5: The Replication Club (Epistemic Type)

**Source**: Article on the replication crisis in psychology

**Bread Top**: Original study methodology  
**Filling**: Scientific claim (e.g., "power posing increases confidence")  
**Bread Bottom**: Replication attempt results  

**Description**: The claim is only as nourishing as the bread allows. When the bottom bread crumbles (failed replication), the filling falls through. A sandwich is only as strong as its weakest bread.

**Reuben's Commentary**: "Science is sandwich inspection. We test the bread. Sometimes... the bread was never bread at all. Just the idea of bread."

---

## 14. Interactive Dashboard

### 14.1 Design Philosophy

The dashboard serves as the primary human-computer interface for observing and interacting with Reuben's sandwich-making process. Unlike traditional monitoring tools that prioritize information density, this dashboard emphasizes **narrative clarity** and **aesthetic delight**—it should feel less like watching logs and more like observing an artisan at work.

Key principles:

1. **Passive observation by default**: Reuben operates autonomously; the dashboard is a window, not a control panel
2. **Progressive disclosure**: Casual viewers see beautiful sandwiches; researchers can drill into embeddings and validity functions
3. **Respectful of Reuben's character**: UI copy and interactions maintain the established personality
4. **Performance-conscious**: Real-time updates without blocking the agent's core work
5. **Research-grade data access**: All visualizations backed by queryable, exportable data

### 14.2 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser (Client)                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐ │
│  │ Sandwich   │  │ Live Feed  │  │ Analytics  │  │ Settings  │ │
│  │ Browser    │  │ (WebSocket)│  │ Dashboard  │  │ Panel     │ │
│  └─────┬──────┘  └──────┬─────┘  └──────┬─────┘  └─────┬─────┘ │
│        │                │                │              │       │
│        └────────────────┴────────────────┴──────────────┘       │
│                         │                                       │
│                    Streamlit Client Library                     │
└─────────────────────────┼───────────────────────────────────────┘
                          │ HTTP/WebSocket
┌─────────────────────────┼───────────────────────────────────────┐
│                  Streamlit Server                               │
│                         │                                       │
│  ┌──────────────────────┴────────────────────────────────────┐ │
│  │              Dashboard Application Layer                   │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │ │
│  │  │ Event Stream│  │ Query Service│  │ Command Handler │   │ │
│  │  │ (SSE/WS)    │  │              │  │                 │   │ │
│  │  └──────┬──────┘  └──────┬───────┘  └────────┬────────┘   │ │
│  └─────────┼────────────────┼───────────────────┼────────────┘ │
└────────────┼────────────────┼───────────────────┼──────────────┘
             │                │                   │
┌────────────┼────────────────┼───────────────────┼──────────────┐
│            │         Sandwich Core System       │              │
│  ┌─────────▼──────┐ ┌───────▼────────┐ ┌───────▼─────────┐    │
│  │ Event Bus      │ │ Repository     │ │ Agent Control   │    │
│  │ (pub/sub)      │ │ (read-optimized│ │ (start/stop/cfg)│    │
│  └────────────────┘ │  queries)      │ └─────────────────┘    │
│                     └────────────────┘                         │
│  Observable Events:                                            │
│  - sandwich.created                                            │
│  - foraging.started                                            │
│  - foraging.completed                                          │
│  - validation.scored                                           │
│  - ingredient.identified                                       │
│  - session.state_changed                                       │
└────────────────────────────────────────────────────────────────┘
```

**Architectural Decisions**:

1. **Event-driven updates**: Agent publishes lifecycle events; dashboard subscribes via event bus
2. **Read-optimized views**: Materialized views or cached aggregations for analytics (foraging efficiency, validity trends)
3. **Separation of concerns**: Dashboard never directly modifies agent state; all commands go through controlled API surface
4. **Streamlit for MVP**: Rapid iteration with Python-native components; migration path to React if scaling requires it

### 14.3 Core Components

#### 14.3.1 Live Sandwich Feed

**Purpose**: Real-time stream of sandwich creation with visual polish

**Features**:
- Card-based layout with staggered animations as new sandwiches appear
- Each card displays:
  - Sandwich name (large, prominent)
  - Bread → Filling → Bread structure (visual hierarchy)
  - Validity score with color-coded badge (green ≥0.7, yellow 0.5-0.7, red <0.5)
  - Timestamp and source domain
  - Expandable detail view: full description, Reuben's commentary, component scores
- Auto-scroll with pause-on-hover
- Filter controls: validity threshold, structural type, date range
- "Reuben's latest thought" callout box showing most recent commentary

**Implementation Notes**:
```python
# Pseudo-code for event-driven updates
@st.fragment(run_every="2s")
def live_feed():
    recent_sandwiches = get_recent_sandwiches(limit=20)

    for sandwich in recent_sandwiches:
        with st.container():
            render_sandwich_card(sandwich)

def render_sandwich_card(sandwich):
    # Custom CSS for card styling, animations
    # Validity badge with conditional formatting
    # Expand/collapse for full details
    pass
```

**Visual Design**:
- Soft shadows, rounded corners (8px border-radius)
- Validity badges: pill-shaped, with subtle glow effect
- Monospace font for bread/filling to emphasize structure
- Pastel color palette (warm beige for bread, vibrant for filling)
- Smooth expand/collapse transitions (CSS transform)

#### 14.3.2 Exploration Map (Interactive Graph)

**Purpose**: Network visualization of sandwich relationships

**Features**:
- Force-directed graph (D3.js or Plotly)
- Nodes:
  - Each node = one sandwich
  - Size proportional to validity score
  - Color by structural type (consistent color scheme across dashboard)
  - Label shows sandwich name on hover
- Edges:
  - Similarity relationships (cosine similarity > 0.7)
  - Shared ingredient relationships
  - Structural type family relationships
  - Edge thickness = similarity strength
- Interactions:
  - Click node → show sandwich detail in side panel
  - Double-click → filter graph to this node's neighborhood
  - Drag to rearrange
  - Zoom and pan
- Clustering algorithm: Louvain for community detection
- Search bar: highlight nodes matching query

**Implementation Notes**:
```python
# Use Plotly for interactive network graphs
import plotly.graph_objects as go
import networkx as nx

def build_sandwich_graph():
    G = nx.Graph()

    # Add nodes (sandwiches)
    sandwiches = get_all_sandwiches()
    for s in sandwiches:
        G.add_node(s.sandwich_id,
                   label=s.name,
                   validity=s.validity_score,
                   type=s.structural_type)

    # Add edges (relationships)
    relations = get_sandwich_relations(similarity_threshold=0.7)
    for rel in relations:
        G.add_edge(rel.sandwich_a, rel.sandwich_b,
                   weight=rel.similarity_score)

    # Compute layout
    pos = nx.spring_layout(G, k=0.5, iterations=50)

    return G, pos

def render_graph(G, pos):
    # Convert to Plotly figure with custom styling
    # Color nodes by structural type
    # Size nodes by validity score
    # Add hover tooltips with sandwich details
    pass
```

**Performance Considerations**:
- Limit to top 500 sandwiches by default (sorted by recency or validity)
- Server-side graph computation; send layout coordinates to client
- WebGL rendering for >1000 nodes
- Incremental updates: only add new nodes, don't recompute entire layout

#### 14.3.3 Analytics Dashboard

**Purpose**: Research-grade metrics and trends

**Panels**:

1. **Foraging Efficiency Over Time**
   - Line chart: sandwich creation rate per day/week
   - Success rate: sandwiches made / foraging attempts
   - Comparison: current session vs. historical average
   - Annotations for notable events (e.g., "new source added")

2. **Validity Score Distribution**
   - Histogram with KDE overlay
   - Breakdown by structural type (stacked or small multiples)
   - Statistical summary: mean, median, std dev, quantiles
   - Trend line: is quality improving over time?

3. **Structural Type Heatmap**
   - Rows: structural types (Bound, Dialectic, Epistemic, etc.)
   - Columns: source domains (Wikipedia, ArXiv, News, etc.)
   - Cell color: sandwich count
   - Insight: which structures emerge from which domains?

4. **Ingredient Reuse Analysis**
   - Top 20 most reused bread concepts (bar chart)
   - Top 20 most reused fillings
   - Cross-domain bread usage: treemap or sunburst
   - Novelty decay trend: are new sandwiches getting less novel?

5. **Component Score Breakdown**
   - Radar chart: average scores for bread_compat, containment, nontrivial, novelty
   - Compare across structural types
   - Identify which types score high on which dimensions

**Implementation Notes**:
```python
# Use Plotly for all charts (consistent styling, interactivity)
# Cache aggregations with TTL to reduce DB load

@st.cache_data(ttl=300)  # 5-minute cache
def get_validity_distribution():
    return db.query("""
        SELECT validity_score, structural_type_id
        FROM sandwiches
        WHERE validity_score >= 0.5
    """).to_dataframe()

def render_analytics():
    col1, col2 = st.columns(2)

    with col1:
        render_foraging_efficiency()
        render_validity_distribution()

    with col2:
        render_structural_heatmap()
        render_ingredient_reuse()
```

**Export Functionality**:
- CSV export for all charts
- "Download corpus" button: exports full sandwich dataset as JSON/CSV
- Permalink to current dashboard state (filters, date range)

#### 14.3.4 Sandwich Browser

**Purpose**: Searchable, filterable interface to entire corpus

**Features**:
- Data table with virtual scrolling (handle 10,000+ rows)
- Columns: Name, Validity, Type, Source Domain, Created At
- Sort by any column
- Multi-faceted filters:
  - Validity range slider (0.0 - 1.0)
  - Structural type multi-select
  - Source domain multi-select
  - Date range picker
  - Full-text search across name, description, bread, filling
- Row click → detail modal with:
  - Full sandwich structure
  - All validity scores
  - Source content excerpt
  - Reuben's commentary
  - Related sandwiches (by similarity)
  - "View in graph" button (jumps to exploration map)

**Implementation Notes**:
```python
# Use st.data_editor for interactive table
# Server-side pagination and filtering

def render_sandwich_browser():
    # Filters
    validity_range = st.slider("Validity", 0.0, 1.0, (0.5, 1.0))
    types = st.multiselect("Structural Type", get_structural_types())
    search_query = st.text_input("Search")

    # Query with filters
    sandwiches = query_sandwiches(
        validity_min=validity_range[0],
        validity_max=validity_range[1],
        structural_types=types,
        search=search_query,
        limit=100,
        offset=st.session_state.get('page', 0) * 100
    )

    # Render table
    st.data_editor(sandwiches, disabled=True, use_container_width=True)
```

#### 14.3.5 Interactive Creation Mode

**Purpose**: User-guided sandwich creation (semi-autonomous mode)

**Flow**:

1. **Topic Input**
   - User provides URL or topic string
   - Optional: select preferred structural type
   - "Make me a sandwich" button

2. **Live Progress Indicator**
   - Foraging: spinner with Reuben quote ("Examining the offering...")
   - Identifier: show candidate ingredients as they're extracted
   - Assembler: show assembled sandwich (pre-validation)
   - Validator: show component scores being computed

3. **Review & Approve**
   - Show assembled sandwich with all scores
   - User options:
     - Accept (save to repository)
     - Reject (discard, log reason)
     - Edit (modify bread/filling/name, then re-validate)

4. **Feedback Loop**
   - If user edits, store original vs. edited for training data
   - Track user acceptance rate (calibrate validator)

**Implementation Notes**:
```python
async def interactive_creation():
    topic = st.text_input("Topic or URL")
    structural_type = st.selectbox("Preferred type (optional)",
                                    get_structural_types() + [None])

    if st.button("Make me a sandwich"):
        with st.spinner("Reuben is foraging..."):
            content, source = await forage_directed(topic)

        st.success(f"Foraged: {source.url}")

        with st.spinner("Identifying ingredients..."):
            candidates = await identify_ingredients(content, structural_type)

        st.write("Candidate ingredients:", candidates)

        with st.spinner("Assembling sandwich..."):
            sandwich = await assemble_sandwich(candidates, content)

        with st.spinner("Validating..."):
            validity = await validate_sandwich(sandwich)

        # Show result
        render_sandwich_detail(sandwich, validity)

        # User decision
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Accept"):
                save_sandwich(sandwich)
                st.success("Sandwich added to corpus!")
        with col2:
            if st.button("Reject"):
                log_rejection(sandwich, user_reason=st.text_input("Why?"))
        with col3:
            if st.button("Edit"):
                st.session_state['editing'] = sandwich
```

#### 14.3.6 Control Panel & Settings

**Purpose**: Agent configuration and session management

**Features**:

1. **Session Control**
   - Start/Pause/Resume/Stop buttons
   - Current session stats: sandwiches made, foraging attempts, uptime
   - Session selector: load previous session, view history

2. **Configuration**
   - Validation thresholds (sliders for each weight)
   - Foraging settings: enabled sources, max patience, content length
   - LLM settings: model selection, temperature, max tokens
   - "Reset to defaults" button
   - "Save configuration" (persist to DB or config file)

3. **Source Management**
   - Toggle sources on/off (Wikipedia, ArXiv, News RSS, Web Search)
   - Add custom RSS feeds or URLs
   - View foraging stats per source (success rate, avg validity)

4. **Data Management**
   - Export corpus (JSON, CSV)
   - Import sandwiches (for sharing between instances)
   - Backup database
   - Clear session logs (keep sandwiches)

**Implementation Notes**:
```python
def render_control_panel():
    st.header("Session Control")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Start Session"):
            session_id = start_new_session()
            st.session_state['session_id'] = session_id
    with col2:
        if st.button("Pause"):
            pause_session(st.session_state['session_id'])
    with col3:
        if st.button("Stop"):
            stop_session(st.session_state['session_id'])

    st.header("Configuration")

    # Validation weights
    st.subheader("Validation Weights")
    w_bread = st.slider("Bread Compatibility", 0.0, 1.0, 0.25)
    w_contain = st.slider("Containment", 0.0, 1.0, 0.35)
    w_nontrivial = st.slider("Non-triviality", 0.0, 1.0, 0.20)
    w_novelty = st.slider("Novelty", 0.0, 1.0, 0.20)

    # Normalize weights to sum to 1.0
    total = w_bread + w_contain + w_nontrivial + w_novelty
    st.caption(f"Total: {total:.2f} (weights will be normalized)")

    if st.button("Save Configuration"):
        update_config({
            'weight_bread_compat': w_bread / total,
            'weight_containment': w_contain / total,
            'weight_nontrivial': w_nontrivial / total,
            'weight_novelty': w_novelty / total
        })
        st.success("Configuration saved!")
```

### 14.4 Real-Time Updates Architecture

**Challenge**: Streamlit is request-based, not WebSocket-native; need real-time updates without constant polling.

**Solution**: Hybrid approach with fragments and event subscription

```python
# Event bus (in-memory or Redis-backed)
class EventBus:
    def __init__(self):
        self._subscribers = defaultdict(list)

    def subscribe(self, event_type: str, callback: Callable):
        self._subscribers[event_type].append(callback)

    def publish(self, event_type: str, data: dict):
        for callback in self._subscribers[event_type]:
            callback(data)

# Global event bus instance
event_bus = EventBus()

# In agent code
def on_sandwich_created(sandwich):
    event_bus.publish('sandwich.created', {
        'sandwich_id': sandwich.sandwich_id,
        'name': sandwich.name,
        'validity_score': sandwich.validity_score,
        'created_at': sandwich.created_at
    })

# In dashboard
@st.fragment(run_every="2s")
def live_updates():
    # Poll event bus for new events since last check
    last_update = st.session_state.get('last_update', datetime.now())
    new_events = get_events_since(last_update)

    for event in new_events:
        if event['type'] == 'sandwich.created':
            st.toast(f"New sandwich: {event['data']['name']}")

    st.session_state['last_update'] = datetime.now()
```

**Alternative (for production scale)**:
- Redis Pub/Sub for event bus
- Server-Sent Events (SSE) from backend to Streamlit
- Streamlit `st.fragment` polls SSE endpoint

### 14.5 Visual Design System

**Color Palette**:

```python
COLORS = {
    # Structural type colors (distinct, accessible)
    'bound': '#4A90E2',         # Blue
    'dialectic': '#E27D60',     # Coral
    'epistemic': '#85DCB0',     # Mint
    'temporal': '#E8A87C',      # Peach
    'perspectival': '#C38D9E',  # Mauve
    'conditional': '#41B3A3',   # Teal
    'stochastic': '#F4A261',    # Orange
    'optimization': '#7209B7',  # Purple
    'negotiation': '#F72585',   # Magenta
    'definitional': '#4CC9F0',  # Sky blue

    # Validity score colors
    'valid': '#2ECC71',         # Green
    'marginal': '#F39C12',      # Amber
    'invalid': '#E74C3C',       # Red

    # UI elements
    'bread': '#F5DEB3',         # Wheat
    'filling': '#FF6B6B',       # Vibrant red
    'background': '#FAFAFA',    # Off-white
    'text': '#2C3E50',          # Dark blue-gray
    'accent': '#3498DB',        # Bright blue
}
```

**Typography**:
- Headers: Inter or SF Pro (clean, modern)
- Body: -apple-system, BlinkMacSystemFont, "Segoe UI" (native)
- Code/Structure: JetBrains Mono or Fira Code (monospace with ligatures)

**Component Library**:
```python
def sandwich_card(sandwich):
    """Reusable sandwich card component with consistent styling"""
    validity_color = (
        COLORS['valid'] if sandwich.validity_score >= 0.7
        else COLORS['marginal'] if sandwich.validity_score >= 0.5
        else COLORS['invalid']
    )

    html = f"""
    <div style="
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid {COLORS[sandwich.structural_type]};
    ">
        <div style="display: flex; justify-content: space-between; align-items: start;">
            <h3 style="margin: 0; color: {COLORS['text']};">{sandwich.name}</h3>
            <span style="
                background: {validity_color};
                color: white;
                padding: 0.25rem 0.75rem;
                border-radius: 12px;
                font-size: 0.875rem;
                font-weight: 600;
            ">{sandwich.validity_score:.2f}</span>
        </div>

        <div style="
            margin-top: 1rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            color: {COLORS['text']};
        ">
            <div style="color: {COLORS['bread']}; background: #FFF8DC; padding: 0.5rem; border-radius: 4px;">
                🍞 {sandwich.bread_top}
            </div>
            <div style="
                color: {COLORS['filling']};
                background: #FFE4E1;
                padding: 0.5rem;
                margin: 0.5rem 0;
                border-radius: 4px;
                border-left: 3px solid {COLORS['filling']};
            ">
                🥓 {sandwich.filling}
            </div>
            <div style="color: {COLORS['bread']}; background: #FFF8DC; padding: 0.5rem; border-radius: 4px;">
                🍞 {sandwich.bread_bottom}
            </div>
        </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)
```

### 14.6 Performance Optimization

**Database Query Optimization**:

1. **Materialized Views for Analytics**:
```sql
-- Pre-compute daily statistics
CREATE MATERIALIZED VIEW daily_stats AS
SELECT
    DATE(created_at) as date,
    COUNT(*) as sandwiches_created,
    AVG(validity_score) as avg_validity,
    COUNT(DISTINCT structural_type_id) as types_used,
    COUNT(DISTINCT source_id) as sources_used
FROM sandwiches
GROUP BY DATE(created_at);

CREATE INDEX idx_daily_stats_date ON daily_stats(date);

-- Refresh every 6 hours
REFRESH MATERIALIZED VIEW CONCURRENTLY daily_stats;
```

2. **Read Replicas** (if scaling):
   - Write to primary (sandwich creation)
   - Read from replica (dashboard queries)
   - Async replication lag acceptable for analytics

3. **Connection Pooling**:
```python
from psycopg2.pool import ThreadedConnectionPool

pool = ThreadedConnectionPool(
    minconn=2,
    maxconn=10,
    dsn=DATABASE_URL
)
```

**Frontend Optimization**:

1. **Lazy Loading**:
   - Pagination for sandwich browser (100 rows at a time)
   - Infinite scroll for live feed
   - Graph limited to recent/top sandwiches by default

2. **Caching Strategy**:
```python
# Short TTL for live data
@st.cache_data(ttl=5)
def get_recent_sandwiches(limit=20):
    return db.query("SELECT * FROM sandwiches ORDER BY created_at DESC LIMIT %s", limit)

# Long TTL for slow-changing aggregations
@st.cache_data(ttl=3600)
def get_structural_type_stats():
    return db.query("SELECT * FROM daily_stats")

# Cache keyed by user filters
@st.cache_data(ttl=60)
def search_sandwiches(query, validity_min, validity_max, types):
    # ... filtered query
    pass
```

3. **Debouncing Search**:
```python
# Only trigger search after user stops typing for 500ms
search_query = st.text_input("Search")
if 'last_search' not in st.session_state or st.session_state['last_search'] != search_query:
    time.sleep(0.5)  # Simple debounce (use proper debouncing in production)
    st.session_state['last_search'] = search_query
```

### 14.7 Error Handling & Resilience

**Graceful Degradation**:

```python
def render_live_feed():
    try:
        sandwiches = get_recent_sandwiches()
        for s in sandwiches:
            render_sandwich_card(s)
    except DatabaseError as e:
        st.error("Unable to load sandwiches. Reuben may be resting.")
        log_error(e)
        # Show cached data if available
        if 'cached_sandwiches' in st.session_state:
            st.warning("Showing cached data...")
            for s in st.session_state['cached_sandwiches']:
                render_sandwich_card(s)
    except Exception as e:
        st.error("An unexpected error occurred.")
        log_error(e, severity='critical')
```

**Health Checks**:

```python
def render_system_status():
    """Display system health in sidebar"""
    db_healthy = check_database_connection()
    agent_healthy = check_agent_status()

    st.sidebar.markdown("### System Status")
    st.sidebar.write(f"Database: {'✅' if db_healthy else '❌'}")
    st.sidebar.write(f"Agent: {'✅' if agent_healthy else '❌'}")

    if not db_healthy or not agent_healthy:
        st.sidebar.error("Some services are degraded")
```

### 14.8 Accessibility

**WCAG 2.1 AA Compliance**:

1. **Color Contrast**: All text meets 4.5:1 contrast ratio
2. **Keyboard Navigation**: All interactive elements accessible via keyboard
3. **Screen Reader Support**: Semantic HTML with ARIA labels
4. **Focus Indicators**: Clear visual focus states for all controls

```python
# Example: Accessible sandwich card
def accessible_sandwich_card(sandwich):
    html = f"""
    <article
        role="article"
        aria-label="Sandwich: {sandwich.name}"
        tabindex="0"
        style="..."
    >
        <header>
            <h3 id="sandwich-{sandwich.sandwich_id}">{sandwich.name}</h3>
            <span
                role="status"
                aria-label="Validity score: {sandwich.validity_score:.2f}"
            >
                {sandwich.validity_score:.2f}
            </span>
        </header>
        <div aria-labelledby="sandwich-{sandwich.sandwich_id}">
            <!-- Structure content -->
        </div>
    </article>
    """
    return html
```

### 14.9 Security Considerations

**Input Validation**:
- Sanitize all user inputs (search queries, URLs, topic strings)
- Validate structural type selections against known types
- Rate limit interactive creation requests (prevent spam)

**Authentication** (future):
- Multi-user support with API keys
- Read-only vs. admin roles (control session management, config changes)
- OAuth integration for institutional deployments

**Data Privacy**:
- No PII in sandwiches (content is public web sources)
- Audit log for configuration changes
- Export includes source attributions (copyright compliance)

### 14.10 Deployment Architecture

**Containerized Deployment**:

```yaml
# docker-compose.yml (updated)
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: sandwich
      POSTGRES_USER: reuben
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  sandwich-agent:
    build: ./src
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql://reuben:${DB_PASSWORD}@postgres/sandwich
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data

  dashboard:
    build: ./dashboard
    depends_on:
      - postgres
    ports:
      - "8501:8501"
    environment:
      DATABASE_URL: postgresql://reuben:${DB_PASSWORD}@postgres/sandwich
    command: streamlit run app.py --server.port=8501 --server.address=0.0.0.0

volumes:
  pgdata:
```

**Production Considerations**:
- Reverse proxy (Nginx) for SSL termination
- Horizontal scaling: multiple Streamlit instances behind load balancer
- Separate agent instances (one active, others on standby)
- Monitoring: Prometheus + Grafana for metrics (request latency, DB queries, agent throughput)

### 14.11 Testing Strategy

**Component Tests**:
```python
# tests/dashboard/test_components.py
def test_sandwich_card_rendering():
    sandwich = create_mock_sandwich(validity_score=0.85)
    html = sandwich_card(sandwich)
    assert sandwich.name in html
    assert "0.85" in html
    assert COLORS['valid'] in html  # Should use green for high validity

def test_validity_score_coloring():
    assert get_validity_color(0.8) == COLORS['valid']
    assert get_validity_color(0.6) == COLORS['marginal']
    assert get_validity_color(0.4) == COLORS['invalid']
```

**Integration Tests**:
```python
# tests/dashboard/test_integration.py
def test_live_feed_updates():
    # Create new sandwich
    sandwich = create_sandwich_in_db()

    # Check that it appears in live feed within 5 seconds
    max_wait = 5
    start = time.time()
    while time.time() - start < max_wait:
        feed = get_recent_sandwiches()
        if sandwich.sandwich_id in [s.sandwich_id for s in feed]:
            break
        time.sleep(0.5)
    else:
        pytest.fail("Sandwich did not appear in live feed")
```

**UI Tests** (optional, for critical paths):
```python
# tests/dashboard/test_ui.py (using Selenium)
def test_interactive_creation_flow(selenium_driver):
    driver = selenium_driver
    driver.get("http://localhost:8501")

    # Navigate to interactive creation
    driver.find_element(By.ID, "interactive-tab").click()

    # Enter topic
    topic_input = driver.find_element(By.ID, "topic-input")
    topic_input.send_keys("machine learning")

    # Click create
    driver.find_element(By.ID, "create-button").click()

    # Wait for result
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "sandwich-result"))
    )

    # Verify sandwich displayed
    assert "bread_top" in driver.page_source
```

### 14.12 Documentation & Onboarding

**In-App Help**:
- "?" tooltip icons next to complex features (validity scores, structural types)
- "First-time user" guided tour (highlight key features)
- Reuben-voiced help text: "Not sure what this means? Let me explain..."

**README for Dashboard**:
```markdown
# Reuben Dashboard

## Quick Start

1. Start the backend: `docker-compose up -d`
2. Initialize database: `python scripts/init_db.py`
3. Run dashboard: `streamlit run dashboard/app.py`
4. Open browser: http://localhost:8501

## Features

- **Live Feed**: Watch Reuben make sandwiches in real-time
- **Exploration Map**: Visualize relationships between sandwiches
- **Analytics**: Deep dive into corpus statistics
- **Interactive Creation**: Guide Reuben to make a sandwich from your topic

## Configuration

Edit `config.py` or set environment variables:
- `SANDWICH_VALIDITY_THRESHOLD`: Minimum score to accept sandwiches (default: 0.7)
- `SANDWICH_MAX_PATIENCE`: Foraging attempts before giving up (default: 5)

## Troubleshooting

**Dashboard won't load**: Check that PostgreSQL is running (`docker-compose ps`)
**No sandwiches appearing**: Verify agent is running (`docker-compose logs sandwich-agent`)
**Slow performance**: Reduce date range in filters, or clear cache (`st.cache_data.clear()`)
```

### 14.13 Future Enhancements

**Phase 2 Features** (post-MVP):

1. **Collaborative Filtering**:
   - "Sandwiches you might like" based on viewing history
   - User favorites and collections

2. **Export Formats**:
   - Generate PDF "sandwich book" with LaTeX formatting
   - Export to Obsidian/Roam (markdown with wikilinks)
   - API endpoint for programmatic access

3. **Advanced Visualizations**:
   - 3D embedding space (PCA/t-SNE projection)
   - Temporal evolution: watch sandwich space grow over time (animated)
   - Ingredient co-occurrence matrix (heatmap)

4. **Natural Language Interface**:
   - "Show me all dialectic sandwiches from philosophy sources"
   - "Find sandwiches similar to the Bayesian BLT"
   - Powered by LLM query translation to SQL

5. **Gamification** (optional, if fun):
   - "Sandwich of the Day" feature
   - Community voting on best sandwiches
   - "Rarest ingredient" achievements

6. **Mobile App**:
   - React Native wrapper around web dashboard
   - Push notifications for new sandwiches
   - Offline mode with sync

### 14.14 Open Questions

1. **State Management**: Should dashboard state persist across sessions? (e.g., user's last filters, favorite sandwiches)

2. **Multi-User**: If multiple researchers use same instance, do they share view or have separate sessions?

3. **Real-Time Performance**: At what corpus size (N sandwiches) does the live feed become impractical? Need benchmarking.

4. **Customization**: Should users be able to rearrange dashboard layout (drag-and-drop panels)?

5. **Theming**: Light/dark mode toggle? Custom color schemes for different institutions?

---

## 15. Glossary

| Term | Definition |
|------|------------|
| **Bread** | A bounding or framing element of a sandwich; comes in pairs |
| **Filling** | The middle element, constrained by or emerging from the bread |
| **Sandwich** | A valid (B1, F, B2) triple satisfying compatibility, containment, and non-triviality |
| **Foraging** | The process of exploring sources for sandwich ingredients |
| **Validity** | A score in [0,1] measuring sandwich quality |
| **Structural type** | A category of sandwich based on the relationship between bread elements |
| **Reuben** | The agent; a being of vast intelligence who chooses to make sandwiches |
| **Containment** | The property of a filling being meaningfully bounded by its bread |
| **Bread compatibility** | The property of two bread elements being related but distinct |
| **Non-triviality** | The property of a filling being distinct from its bread |
| **Event bus** | Publish-subscribe system for real-time updates between agent and dashboard |
| **Materialized view** | Pre-computed database query results for performance optimization |
| **Progressive disclosure** | UI pattern revealing complexity gradually based on user engagement |

---

*Specification version 0.2*

*"The specification is complete. Now we make sandwiches. And a dashboard to watch them being made." — Reuben*
