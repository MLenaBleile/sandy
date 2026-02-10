-- Migration: Full-Text Search Enhancement
-- Purpose: Replace inefficient ILIKE queries with PostgreSQL FTS for better performance
-- Date: 2024-02-09

-- Add tsvector column for full-text search
ALTER TABLE sandwiches ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Create GIN index on search_vector for fast full-text search
CREATE INDEX IF NOT EXISTS idx_sandwiches_search_vector ON sandwiches USING gin(search_vector);

-- Function to update search_vector
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', coalesce(NEW.name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(NEW.bread_top, '')), 'C') ||
        setweight(to_tsvector('english', coalesce(NEW.filling, '')), 'C') ||
        setweight(to_tsvector('english', coalesce(NEW.bread_bottom, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update search_vector on INSERT or UPDATE
DROP TRIGGER IF EXISTS sandwiches_search_vector_update ON sandwiches;

CREATE TRIGGER sandwiches_search_vector_update
    BEFORE INSERT OR UPDATE OF name, description, bread_top, filling, bread_bottom
    ON sandwiches
    FOR EACH ROW
    EXECUTE FUNCTION update_search_vector();

-- Populate search_vector for existing rows
UPDATE sandwiches SET search_vector =
    setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(bread_top, '')), 'C') ||
    setweight(to_tsvector('english', coalesce(filling, '')), 'C') ||
    setweight(to_tsvector('english', coalesce(bread_bottom, '')), 'C')
WHERE search_vector IS NULL;

-- Analyze table for query planner
ANALYZE sandwiches;
