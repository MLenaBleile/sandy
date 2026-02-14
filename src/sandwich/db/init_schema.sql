-- SANDWICH database schema
-- Based on SPEC.md Section 5.2

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Sources: where content comes from
CREATE TABLE IF NOT EXISTS sources (
    source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT,
    domain VARCHAR(255),
    content TEXT,
    content_hash VARCHAR(64),
    fetched_at TIMESTAMP DEFAULT NOW(),
    content_type VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_sources_domain ON sources(domain);
CREATE INDEX IF NOT EXISTS idx_sources_hash ON sources(content_hash);

-- Structural types: taxonomy of sandwich forms
CREATE TABLE IF NOT EXISTS structural_types (
    type_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    bread_relation TEXT,
    filling_role TEXT,
    parent_type_id INT REFERENCES structural_types(type_id),
    canonical_example_id UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sandwiches: the core entity
CREATE TABLE IF NOT EXISTS sandwiches (
    sandwich_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),

    -- Validity assessment
    validity_score FLOAT CHECK (validity_score >= 0 AND validity_score <= 1),
    bread_compat_score FLOAT,
    containment_score FLOAT,
    specificity_score FLOAT,
    nontrivial_score FLOAT,
    novelty_score FLOAT,

    -- The triple (denormalized for query convenience)
    bread_top TEXT NOT NULL,
    bread_bottom TEXT NOT NULL,
    filling TEXT NOT NULL,

    -- Embeddings for similarity search
    bread_top_embedding vector(1536),
    bread_bottom_embedding vector(1536),
    filling_embedding vector(1536),
    sandwich_embedding vector(1536),

    -- Metadata
    source_id UUID REFERENCES sources(source_id),
    structural_type_id INT REFERENCES structural_types(type_id),
    assembly_rationale TEXT,
    validation_rationale TEXT,
    sandy_commentary TEXT
);

CREATE INDEX IF NOT EXISTS idx_sandwiches_validity ON sandwiches(validity_score);
CREATE INDEX IF NOT EXISTS idx_sandwiches_type ON sandwiches(structural_type_id);
CREATE INDEX IF NOT EXISTS idx_sandwiches_created ON sandwiches(created_at);

-- Add FK for canonical example (after sandwiches table exists)
ALTER TABLE structural_types
    ADD CONSTRAINT fk_canonical_example
    FOREIGN KEY (canonical_example_id) REFERENCES sandwiches(sandwich_id);

-- Ingredients: reusable bread and filling concepts
CREATE TABLE IF NOT EXISTS ingredients (
    ingredient_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    text TEXT NOT NULL,
    ingredient_type VARCHAR(20) CHECK (ingredient_type IN ('bread', 'filling')),
    embedding vector(1536),
    first_seen_sandwich UUID REFERENCES sandwiches(sandwich_id),
    first_seen_at TIMESTAMP DEFAULT NOW(),
    usage_count INT DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_ingredients_type ON ingredients(ingredient_type);
CREATE INDEX IF NOT EXISTS idx_ingredients_usage ON ingredients(usage_count DESC);

-- Junction table: sandwiches use ingredients
CREATE TABLE IF NOT EXISTS sandwich_ingredients (
    sandwich_id UUID REFERENCES sandwiches(sandwich_id) ON DELETE CASCADE,
    ingredient_id UUID REFERENCES ingredients(ingredient_id),
    role VARCHAR(20) CHECK (role IN ('bread_top', 'bread_bottom', 'filling')),
    PRIMARY KEY (sandwich_id, ingredient_id, role)
);

-- Relations between sandwiches
CREATE TABLE IF NOT EXISTS sandwich_relations (
    relation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sandwich_a UUID REFERENCES sandwiches(sandwich_id) ON DELETE CASCADE,
    sandwich_b UUID REFERENCES sandwiches(sandwich_id) ON DELETE CASCADE,
    relation_type VARCHAR(50),
    similarity_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    rationale TEXT,
    UNIQUE (sandwich_a, sandwich_b, relation_type)
);

CREATE INDEX IF NOT EXISTS idx_relations_type ON sandwich_relations(relation_type);

-- Foraging log: Sandy's browsing history
CREATE TABLE IF NOT EXISTS foraging_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP DEFAULT NOW(),
    source_id UUID REFERENCES sources(source_id),
    curiosity_prompt TEXT,
    outcome VARCHAR(50),
    outcome_rationale TEXT,
    sandwich_id UUID REFERENCES sandwiches(sandwich_id),
    session_id UUID
);

CREATE INDEX IF NOT EXISTS idx_foraging_session ON foraging_log(session_id);
CREATE INDEX IF NOT EXISTS idx_foraging_outcome ON foraging_log(outcome);

-- LLM call log: observability for all LLM API calls
CREATE TABLE IF NOT EXISTS llm_call_log (
    call_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP DEFAULT NOW(),
    component VARCHAR(50),
    model VARCHAR(100),
    prompt_hash VARCHAR(64),
    input_tokens INT DEFAULT 0,
    output_tokens INT DEFAULT 0,
    latency_ms FLOAT DEFAULT 0,
    cost_usd FLOAT DEFAULT 0,
    error TEXT,
    session_id UUID
);

CREATE INDEX IF NOT EXISTS idx_llm_call_session ON llm_call_log(session_id);
CREATE INDEX IF NOT EXISTS idx_llm_call_component ON llm_call_log(component);
CREATE INDEX IF NOT EXISTS idx_llm_call_timestamp ON llm_call_log(timestamp);

-- Human ratings: visitor feedback on sandwich quality
CREATE TABLE IF NOT EXISTS human_ratings (
    rating_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sandwich_id UUID REFERENCES sandwiches(sandwich_id) ON DELETE SET NULL,
    session_id UUID NOT NULL,

    -- Component scores (matching Sandy's dimensions)
    bread_compat_score FLOAT NOT NULL,
    containment_score FLOAT NOT NULL,
    nontrivial_score FLOAT NOT NULL,
    novelty_score FLOAT NOT NULL,
    overall_validity FLOAT NOT NULL,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    user_agent TEXT,
    ip_hash TEXT,  -- SHA256 hash for privacy, anti-spam

    -- Constraints
    CONSTRAINT valid_bread_compat CHECK (bread_compat_score BETWEEN 0 AND 1),
    CONSTRAINT valid_containment CHECK (containment_score BETWEEN 0 AND 1),
    CONSTRAINT valid_nontrivial CHECK (nontrivial_score BETWEEN 0 AND 1),
    CONSTRAINT valid_novelty CHECK (novelty_score BETWEEN 0 AND 1),
    CONSTRAINT valid_overall CHECK (overall_validity BETWEEN 0 AND 1),

    -- Prevent duplicate ratings from same session
    CONSTRAINT unique_session_sandwich UNIQUE (session_id, sandwich_id)
);

CREATE INDEX IF NOT EXISTS idx_ratings_sandwich ON human_ratings(sandwich_id);
CREATE INDEX IF NOT EXISTS idx_ratings_session ON human_ratings(session_id);
CREATE INDEX IF NOT EXISTS idx_ratings_created ON human_ratings(created_at DESC);

-- Function to get human consensus for a sandwich
CREATE OR REPLACE FUNCTION get_human_consensus(p_sandwich_id UUID)
RETURNS TABLE (
    rating_count BIGINT,
    avg_bread_compat FLOAT,
    avg_containment FLOAT,
    avg_nontrivial FLOAT,
    avg_novelty FLOAT,
    avg_overall FLOAT,
    std_overall FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT,
        AVG(bread_compat_score)::FLOAT,
        AVG(containment_score)::FLOAT,
        AVG(nontrivial_score)::FLOAT,
        AVG(novelty_score)::FLOAT,
        AVG(overall_validity)::FLOAT,
        STDDEV(overall_validity)::FLOAT
    FROM human_ratings
    WHERE sandwich_id = p_sandwich_id;
END;
$$ LANGUAGE plpgsql;

-- Materialized view for dashboard analytics
-- Pre-computes daily statistics for faster dashboard queries
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_stats AS
SELECT
    DATE(created_at) as date,
    COUNT(*) as sandwiches_created,
    AVG(validity_score) as avg_validity,
    COUNT(DISTINCT structural_type_id) as types_used,
    COUNT(DISTINCT source_id) as sources_used
FROM sandwiches
GROUP BY DATE(created_at);

CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(date);
