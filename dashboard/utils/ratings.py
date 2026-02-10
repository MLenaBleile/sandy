"""Backend logic for human rating system."""

import uuid
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

from dashboard.utils.db import execute_query

logger = logging.getLogger(__name__)


def get_or_create_session_id() -> str:
    """Get or create anonymous session ID for tracking raters.

    Session ID is stored in Streamlit session state and persists
    across page navigation within the same browser session.

    Returns:
        UUID string for this session
    """
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        logger.info(f"Created new session ID: {st.session_state.session_id[:8]}...")

    return st.session_state.session_id


def check_rate_limit(
    session_id: str,
    max_ratings: int = 10,
    window_hours: int = 1
) -> tuple[bool, int]:
    """Check if session has exceeded rate limit.

    Prevents spam by limiting ratings per session per time window.

    Args:
        session_id: Session UUID to check
        max_ratings: Maximum ratings allowed in window
        window_hours: Time window in hours

    Returns:
        Tuple of (is_within_limit, ratings_used)
    """
    query = """
        SELECT COUNT(*) as rating_count
        FROM human_ratings
        WHERE session_id = %s
        AND created_at > NOW() - INTERVAL '%s hours'
    """

    try:
        result = execute_query(query, (session_id, window_hours), fetch_one=True)
        count = result['rating_count'] if result else 0

        return count < max_ratings, count

    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        # Fail open - allow rating if check fails
        return True, 0


def has_rated_sandwich(session_id: str, sandwich_id: str) -> bool:
    """Check if session has already rated this specific sandwich.

    Args:
        session_id: Session UUID
        sandwich_id: Sandwich UUID

    Returns:
        True if already rated
    """
    query = """
        SELECT COUNT(*) as count
        FROM human_ratings
        WHERE session_id = %s AND sandwich_id = %s
    """

    try:
        result = execute_query(query, (session_id, sandwich_id), fetch_one=True)
        return result['count'] > 0 if result else False

    except Exception as e:
        logger.error(f"Has rated check failed: {e}")
        return False  # Fail open


def save_rating(
    sandwich_id: str,
    session_id: str,
    scores: Dict[str, float],
    user_agent: Optional[str] = None,
    ip_hash: Optional[str] = None
) -> bool:
    """Save human rating to database.

    Args:
        sandwich_id: UUID of sandwich being rated
        session_id: UUID of rater's session
        scores: Dict with keys: bread_compat, containment, nontrivial, novelty, overall
        user_agent: Optional user agent string
        ip_hash: Optional hashed IP address for spam prevention

    Returns:
        True if saved successfully
    """
    query = """
        INSERT INTO human_ratings (
            sandwich_id, session_id,
            bread_compat_score, containment_score,
            nontrivial_score, novelty_score, overall_validity,
            user_agent, ip_hash
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (session_id, sandwich_id) DO NOTHING
    """

    try:
        execute_query(query, (
            sandwich_id,
            session_id,
            scores['bread_compat'],
            scores['containment'],
            scores['nontrivial'],
            scores['novelty'],
            scores['overall'],
            user_agent,
            ip_hash
        ))

        logger.info(f"Saved rating for sandwich {sandwich_id[:8]} from session {session_id[:8]}")
        return True

    except Exception as e:
        logger.error(f"Failed to save rating: {e}")
        return False


def get_human_consensus(sandwich_id: str) -> Optional[Dict]:
    """Get aggregated human ratings for a sandwich.

    Args:
        sandwich_id: Sandwich UUID

    Returns:
        Dict with consensus statistics, or None if no ratings
    """
    query = """
        SELECT
            COUNT(*) as rating_count,
            AVG(bread_compat_score) as avg_bread_compat,
            AVG(containment_score) as avg_containment,
            AVG(nontrivial_score) as avg_nontrivial,
            AVG(novelty_score) as avg_novelty,
            AVG(overall_validity) as avg_overall,
            STDDEV(overall_validity) as std_overall
        FROM human_ratings
        WHERE sandwich_id = %s
    """

    try:
        return execute_query(query, (sandwich_id,), fetch_one=True)

    except Exception as e:
        logger.error(f"Failed to get consensus: {e}")
        return None


def get_rating_stats() -> Dict:
    """Get overall rating system statistics.

    Returns:
        Dict with total_ratings, unique_sandwiches, unique_raters
    """
    query = """
        SELECT
            COUNT(*) as total_ratings,
            COUNT(DISTINCT sandwich_id) as unique_sandwiches,
            COUNT(DISTINCT session_id) as unique_raters
        FROM human_ratings
    """

    try:
        return execute_query(query, fetch_one=True) or {
            'total_ratings': 0,
            'unique_sandwiches': 0,
            'unique_raters': 0
        }

    except Exception as e:
        logger.error(f"Failed to get rating stats: {e}")
        return {
            'total_ratings': 0,
            'unique_sandwiches': 0,
            'unique_raters': 0
        }
