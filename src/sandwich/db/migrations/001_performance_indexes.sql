-- Migration: Performance Indexes
-- Purpose: Speed up dashboard queries 10-100x
-- Date: 2024-02-09

-- Index for ORDER BY created_at DESC (Live Feed, Browser)
CREATE INDEX IF NOT EXISTS idx_sandwiches_created_at
ON sandwiches(created_at DESC);

-- Index for validity score filtering
CREATE INDEX IF NOT EXISTS idx_sandwiches_validity
ON sandwiches(validity_score);

-- Index for structural type filtering
CREATE INDEX IF NOT EXISTS idx_sandwiches_type
ON sandwiches(structural_type_id);

-- Composite index for common query patterns (validity + type + time)
CREATE INDEX IF NOT EXISTS idx_sandwiches_validity_type_created
ON sandwiches(validity_score, structural_type_id, created_at DESC);

-- Full-text search indexes using pg_trgm extension
CREATE INDEX IF NOT EXISTS idx_sandwiches_name_trgm
ON sandwiches USING gin(name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_sandwiches_description_trgm
ON sandwiches USING gin(description gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_sandwiches_bread_top_trgm
ON sandwiches USING gin(bread_top gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_sandwiches_filling_trgm
ON sandwiches USING gin(filling gin_trgm_ops);

-- Index for source joins
CREATE INDEX IF NOT EXISTS idx_sandwiches_source
ON sandwiches(source_id);

-- Analyze tables for query planner
ANALYZE sandwiches;
ANALYZE sources;
ANALYZE structural_types;
