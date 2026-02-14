-- Migration: Protect Human Ratings from Cascade Deletion
-- Purpose: Ratings should never be silently destroyed when sandwiches are deleted
-- Date: 2025-02-14

-- Drop the old CASCADE foreign key and replace with SET NULL
-- This means if a sandwich is deleted, the rating rows survive with sandwich_id = NULL

-- Step 1: Make sandwich_id nullable (it was NOT NULL before)
ALTER TABLE human_ratings ALTER COLUMN sandwich_id DROP NOT NULL;

-- Step 2: Drop the existing FK constraint
-- The constraint was created inline, so its auto-generated name varies.
-- Find and drop it dynamically:
DO $$
DECLARE
    fk_name TEXT;
BEGIN
    SELECT constraint_name INTO fk_name
    FROM information_schema.table_constraints
    WHERE table_name = 'human_ratings'
      AND constraint_type = 'FOREIGN KEY'
    LIMIT 1;

    IF fk_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE human_ratings DROP CONSTRAINT %I', fk_name);
        RAISE NOTICE 'Dropped FK constraint: %', fk_name;
    END IF;
END $$;

-- Step 3: Re-add with ON DELETE SET NULL instead of CASCADE
ALTER TABLE human_ratings
    ADD CONSTRAINT fk_ratings_sandwich
    FOREIGN KEY (sandwich_id) REFERENCES sandwiches(sandwich_id)
    ON DELETE SET NULL;
