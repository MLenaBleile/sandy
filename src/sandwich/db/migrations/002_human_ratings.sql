-- Migration: Human Ratings System
-- Purpose: Enable visitor feedback on sandwich quality
-- Date: 2024-02-09

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

-- Indexes for human ratings
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

ANALYZE human_ratings;
