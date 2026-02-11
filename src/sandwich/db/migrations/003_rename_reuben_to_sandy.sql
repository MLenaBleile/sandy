-- Migration: Rename reuben_commentary to sandy_commentary
-- Date: 2026-02-10
-- Purpose: Avoid copyright issues with Disney's character "Reuben" from Lilo & Stitch

BEGIN;

-- Rename the column in the sandwiches table
ALTER TABLE sandwiches
RENAME COLUMN reuben_commentary TO sandy_commentary;

-- No data transformation needed - just a column rename
-- The commentary content itself doesn't need to change

COMMIT;

-- Verification query (run after migration):
-- SELECT sandwich_id, name, sandy_commentary FROM sandwiches LIMIT 5;
