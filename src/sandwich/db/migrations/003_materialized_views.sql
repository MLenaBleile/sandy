-- Migration: Materialized Views for Analytics
-- Purpose: Pre-compute expensive aggregations
-- Date: 2024-02-09

-- View: Structural type statistics by source domain
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_structural_type_stats AS
SELECT
    st.name as structural_type,
    src.domain,
    COUNT(*) as sandwich_count,
    AVG(s.validity_score) as avg_validity,
    AVG(s.bread_compat_score) as avg_bread_compat,
    AVG(s.containment_score) as avg_containment,
    AVG(s.nontrivial_score) as avg_nontrivial,
    AVG(s.novelty_score) as avg_novelty,
    MIN(s.validity_score) as min_validity,
    MAX(s.validity_score) as max_validity
FROM sandwiches s
JOIN structural_types st ON s.structural_type_id = st.type_id
LEFT JOIN sources src ON s.source_id = src.source_id
GROUP BY st.name, src.domain;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_type_stats_unique ON mv_structural_type_stats(structural_type, domain);
CREATE INDEX IF NOT EXISTS idx_mv_type_stats ON mv_structural_type_stats(structural_type);

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW mv_structural_type_stats;
    -- Refresh daily_stats if it exists
    IF EXISTS (SELECT 1 FROM pg_matviews WHERE matviewname = 'daily_stats') THEN
        REFRESH MATERIALIZED VIEW daily_stats;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Initial refresh
SELECT refresh_all_materialized_views();
