"""Dashboard-optimized queries with caching.

All query functions use Streamlit's cache_data decorator with appropriate TTLs
to reduce database load while maintaining reasonable freshness.

Based on plan from Phase 4.2
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional
from .db import execute_query
import logging

logger = logging.getLogger(__name__)


@st.cache_data(ttl=5)
def get_recent_sandwiches(limit: int = 20) -> List[Dict[str, Any]]:
    """Get most recent sandwiches for live feed.

    Args:
        limit: Maximum number of sandwiches to return

    Returns:
        List of sandwich dicts with structural_type name joined
    """
    query = """
        SELECT
            s.sandwich_id,
            s.name,
            s.validity_score,
            s.bread_top,
            s.filling,
            s.bread_bottom,
            s.description,
            s.reuben_commentary,
            s.created_at,
            s.bread_compat_score,
            s.containment_score,
            s.nontrivial_score,
            s.novelty_score,
            st.name as structural_type,
            src.domain
        FROM sandwiches s
        LEFT JOIN structural_types st ON s.structural_type_id = st.type_id
        LEFT JOIN sources src ON s.source_id = src.source_id
        ORDER BY s.created_at DESC
        LIMIT %s
    """

    results = execute_query(query, (limit,))
    return results if results else []


@st.cache_data(ttl=60)
def search_sandwiches(
    query: str = "",
    validity_min: float = 0.0,
    validity_max: float = 1.0,
    types: List[str] = None,
    limit: int = 100,
    offset: int = 0
) -> pd.DataFrame:
    """Search sandwiches with filters.

    Args:
        query: Search query for name/description
        validity_min: Minimum validity score
        validity_max: Maximum validity score
        types: List of structural type names to filter by
        limit: Maximum results
        offset: Offset for pagination

    Returns:
        DataFrame of matching sandwiches
    """
    # Build query dynamically based on filters
    sql = """
        SELECT
            s.sandwich_id,
            s.name,
            s.validity_score,
            s.bread_top,
            s.filling,
            s.bread_bottom,
            s.created_at,
            st.name as structural_type,
            src.domain as source_domain
        FROM sandwiches s
        LEFT JOIN structural_types st ON s.structural_type_id = st.type_id
        LEFT JOIN sources src ON s.source_id = src.source_id
        WHERE s.validity_score BETWEEN %s AND %s
    """

    params = [validity_min, validity_max]

    # Add type filter if provided
    if types and len(types) > 0:
        placeholders = ','.join(['%s'] * len(types))
        sql += f" AND st.name IN ({placeholders})"
        params.extend(types)

    # Add search query if provided
    if query and query.strip():
        sql += " AND (s.name ILIKE %s OR s.description ILIKE %s OR s.bread_top ILIKE %s OR s.filling ILIKE %s OR s.bread_bottom ILIKE %s)"
        search_pattern = f"%{query}%"
        params.extend([search_pattern] * 5)

    sql += " ORDER BY s.created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    results = execute_query(sql, tuple(params))

    # Convert to DataFrame
    if results:
        return pd.DataFrame(results)
    else:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def get_validity_distribution() -> pd.DataFrame:
    """Get validity scores for histogram.

    Returns:
        DataFrame with validity_score and structural_type
    """
    query = """
        SELECT
            s.validity_score,
            st.name as structural_type
        FROM sandwiches s
        LEFT JOIN structural_types st ON s.structural_type_id = st.type_id
        WHERE s.validity_score >= 0.5
    """

    results = execute_query(query)
    return pd.DataFrame(results) if results else pd.DataFrame()


@st.cache_data(ttl=300)
def get_structural_type_stats() -> pd.DataFrame:
    """Get sandwich counts by type and source domain.

    Returns:
        DataFrame with structure_type, domain, sandwich_count
    """
    query = """
        SELECT
            st.name as structure_type,
            src.domain,
            COUNT(*) as sandwich_count
        FROM sandwiches s
        JOIN structural_types st ON s.structural_type_id = st.type_id
        JOIN sources src ON s.source_id = src.source_id
        GROUP BY st.name, src.domain
        ORDER BY sandwich_count DESC
    """

    results = execute_query(query)
    return pd.DataFrame(results) if results else pd.DataFrame()


@st.cache_data(ttl=300)
def get_foraging_efficiency() -> pd.DataFrame:
    """Get foraging attempts and success rate over time.

    Returns:
        DataFrame with date, attempts, successes
    """
    query = """
        SELECT
            DATE(timestamp) as date,
            COUNT(*) as attempts,
            SUM(CASE WHEN outcome = 'sandwich_made' THEN 1 ELSE 0 END) as successes
        FROM foraging_log
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
        LIMIT 30
    """

    results = execute_query(query)
    return pd.DataFrame(results) if results else pd.DataFrame()


@st.cache_data(ttl=300)
def get_component_scores() -> pd.DataFrame:
    """Get average component scores by structural type.

    Returns:
        DataFrame with structural_type and average scores for each component
    """
    query = """
        SELECT
            st.name as structural_type,
            AVG(s.bread_compat_score) as avg_bread_compat,
            AVG(s.containment_score) as avg_containment,
            AVG(s.nontrivial_score) as avg_nontrivial,
            AVG(s.novelty_score) as avg_novelty
        FROM sandwiches s
        JOIN structural_types st ON s.structural_type_id = st.type_id
        WHERE s.bread_compat_score IS NOT NULL
        GROUP BY st.name
    """

    results = execute_query(query)
    return pd.DataFrame(results) if results else pd.DataFrame()


@st.cache_data(ttl=300)
def get_all_component_scores() -> pd.DataFrame:
    """Get all sandwiches with their component scores for statistical analysis.

    Returns:
        DataFrame with sandwich_id, structural_type, and all component scores
    """
    query = """
        SELECT
            s.sandwich_id,
            st.name as structural_type,
            s.validity_score,
            s.bread_compat_score,
            s.containment_score,
            s.nontrivial_score,
            s.novelty_score
        FROM sandwiches s
        JOIN structural_types st ON s.structural_type_id = st.type_id
        WHERE s.bread_compat_score IS NOT NULL
        AND s.containment_score IS NOT NULL
        AND s.nontrivial_score IS NOT NULL
        AND s.novelty_score IS NOT NULL
        ORDER BY s.created_at DESC
    """

    results = execute_query(query)
    return pd.DataFrame(results) if results else pd.DataFrame()


@st.cache_data(ttl=5)
def get_total_sandwich_count() -> int:
    """Get total number of sandwiches in corpus.

    Returns:
        Total sandwich count
    """
    query = "SELECT COUNT(*) as count FROM sandwiches"
    result = execute_query(query, fetch_one=True)
    return result['count'] if result else 0


@st.cache_data(ttl=60)
def get_avg_validity() -> float:
    """Get average validity score across all sandwiches.

    Returns:
        Average validity score
    """
    query = "SELECT AVG(validity_score) as avg_validity FROM sandwiches WHERE validity_score IS NOT NULL"
    result = execute_query(query, fetch_one=True)
    return float(result['avg_validity']) if result and result['avg_validity'] else 0.0


@st.cache_data(ttl=5)
def get_sandwiches_today() -> int:
    """Get number of sandwiches created today.

    Returns:
        Count of today's sandwiches
    """
    query = "SELECT COUNT(*) as count FROM sandwiches WHERE DATE(created_at) = CURRENT_DATE"
    result = execute_query(query, fetch_one=True)
    return result['count'] if result else 0


@st.cache_data(ttl=300)
def get_structural_types() -> List[str]:
    """Get list of all structural type names.

    Returns:
        List of structural type names
    """
    query = "SELECT name FROM structural_types ORDER BY name"
    results = execute_query(query)
    return [r['name'] for r in results] if results else []


@st.cache_data(ttl=300)
def get_source_domains() -> List[str]:
    """Get list of all source domains.

    Returns:
        List of unique source domains
    """
    query = "SELECT DISTINCT domain FROM sources WHERE domain IS NOT NULL ORDER BY domain"
    results = execute_query(query)
    return [r['domain'] for r in results] if results else []


@st.cache_data(ttl=300)
def get_sandwich_relations(similarity_threshold: float = 0.7, limit: int = 500) -> List[Dict[str, Any]]:
    """Get sandwich relationships for graph visualization.

    Args:
        similarity_threshold: Minimum similarity score for edges
        limit: Maximum number of relationships to return

    Returns:
        List of relation dicts
    """
    query = """
        SELECT
            sandwich_a,
            sandwich_b,
            similarity_score,
            relation_type
        FROM sandwich_relations
        WHERE similarity_score >= %s
        ORDER BY similarity_score DESC
        LIMIT %s
    """

    results = execute_query(query, (similarity_threshold, limit))
    return results if results else []


def get_all_sandwiches() -> List[Dict[str, Any]]:
    """Get all sandwiches (for export).

    Note: Not cached as this is used for one-time export.

    Returns:
        List of all sandwich dicts
    """
    query = """
        SELECT
            s.*,
            st.name as structural_type,
            src.url as source_url,
            src.domain as source_domain
        FROM sandwiches s
        LEFT JOIN structural_types st ON s.structural_type_id = st.type_id
        LEFT JOIN sources src ON s.source_id = src.source_id
        ORDER BY s.created_at DESC
    """

    results = execute_query(query)
    return results if results else []


# Human Ratings Queries

@st.cache_data(ttl=30)  # Cache for 30 seconds (semi-real-time)
def get_rating_stats() -> Dict:
    """Get overall rating system statistics."""
    from dashboard.utils.ratings import get_rating_stats as _get_stats
    return _get_stats()


@st.cache_data(ttl=60)
def get_top_rated_sandwiches(limit: int = 10) -> List[Dict[str, Any]]:
    """Get sandwiches with highest human consensus ratings.

    Only includes sandwiches with at least 3 human ratings.
    """
    query = """
        SELECT
            s.*,
            st.name as structural_type,
            AVG(hr.overall_validity) as human_avg,
            COUNT(hr.rating_id) as rating_count
        FROM sandwiches s
        LEFT JOIN structural_types st ON s.structural_type_id = st.type_id
        JOIN human_ratings hr ON s.sandwich_id = hr.sandwich_id
        GROUP BY s.sandwich_id, st.name
        HAVING COUNT(hr.rating_id) >= 3
        ORDER BY AVG(hr.overall_validity) DESC
        LIMIT %s
    """
    results = execute_query(query, (limit,))
    return results if results else []


@st.cache_data(ttl=60)
def get_most_controversial_sandwiches(limit: int = 10) -> List[Dict[str, Any]]:
    """Get sandwiches with highest disagreement between Reuben and humans.

    Only includes sandwiches with at least 3 human ratings.
    """
    query = """
        SELECT
            s.*,
            st.name as structural_type,
            s.validity_score as reuben_score,
            AVG(hr.overall_validity) as human_avg,
            ABS(s.validity_score - AVG(hr.overall_validity)) as disagreement,
            COUNT(hr.rating_id) as rating_count
        FROM sandwiches s
        LEFT JOIN structural_types st ON s.structural_type_id = st.type_id
        JOIN human_ratings hr ON s.sandwich_id = hr.sandwich_id
        GROUP BY s.sandwich_id, st.name
        HAVING COUNT(hr.rating_id) >= 3
        ORDER BY disagreement DESC
        LIMIT %s
    """
    results = execute_query(query, (limit,))
    return results if results else []


@st.cache_data(ttl=60)
def get_reuben_vs_human_comparison() -> List[Dict[str, Any]]:
    """Get comparison data for Reuben vs human scores.

    Returns list of sandwiches with both Reuben and human scores.
    Only includes sandwiches with at least 3 ratings for statistical validity.
    """
    query = """
        SELECT
            s.sandwich_id,
            s.name,
            s.validity_score as reuben_score,
            AVG(hr.overall_validity) as human_score,
            COUNT(hr.rating_id) as rating_count,
            st.name as structural_type
        FROM sandwiches s
        JOIN human_ratings hr ON s.sandwich_id = hr.sandwich_id
        LEFT JOIN structural_types st ON s.structural_type_id = st.type_id
        GROUP BY s.sandwich_id, s.name, s.validity_score, st.name
        HAVING COUNT(hr.rating_id) >= 3
        ORDER BY s.created_at DESC
    """
    results = execute_query(query)
    return results if results else []


@st.cache_data(ttl=60)
def get_component_comparison() -> Dict[str, Any]:
    """Get average component scores for Reuben vs humans."""
    query = """
        SELECT
            AVG(s.bread_compat_score) as reuben_bread,
            AVG(hr.bread_compat_score) as human_bread,
            AVG(s.containment_score) as reuben_contain,
            AVG(hr.containment_score) as human_contain,
            AVG(s.nontrivial_score) as reuben_nontrivial,
            AVG(hr.nontrivial_score) as human_nontrivial,
            AVG(s.novelty_score) as reuben_novelty,
            AVG(hr.novelty_score) as human_novelty
        FROM sandwiches s
        JOIN human_ratings hr ON s.sandwich_id = hr.sandwich_id
    """
    result = execute_query(query, fetch_one=True)
    return result if result else {}
