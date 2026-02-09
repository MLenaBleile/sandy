"""Database connection utilities for the dashboard.

Provides cached database connections for Streamlit dashboard using the same
connection pattern as the main application.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
import logging

logger = logging.getLogger(__name__)


@st.cache_resource
def get_db_connection():
    """Get or create a cached database connection.

    Uses Streamlit's cache_resource decorator to maintain a single connection
    across dashboard sessions. Connection pattern matches the Repository class
    from src/sandwich/db/repository.py.

    Returns:
        psycopg2 connection with RealDictCursor

    Raises:
        psycopg2.Error: If connection fails
    """
    # Try to get DATABASE_URL from env or Streamlit secrets
    database_url = os.getenv('DATABASE_URL')

    if database_url is None and hasattr(st, 'secrets') and 'DATABASE_URL' in st.secrets:
        database_url = st.secrets['DATABASE_URL']

    if database_url is None:
        raise ValueError(
            "DATABASE_URL not found. Set environment variable or add to Streamlit secrets."
        )

    logger.info(f"Connecting to database...")

    conn = psycopg2.connect(
        database_url,
        cursor_factory=RealDictCursor
    )

    # Register UUID adapter (same as Repository)
    psycopg2.extras.register_uuid()

    logger.info("Database connection established")

    return conn


def check_database_connection() -> bool:
    """Check if database connection is healthy.

    Returns:
        True if connection is working, False otherwise
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
        return result is not None
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def execute_query(query: str, params: tuple = None, fetch_one: bool = False):
    """Execute a query and return results.

    Args:
        query: SQL query string
        params: Query parameters (for parameterized queries)
        fetch_one: If True, return single row instead of list

    Returns:
        Single dict if fetch_one=True, otherwise list of dicts
    """
    conn = get_db_connection()

    with conn.cursor() as cur:
        cur.execute(query, params or ())

        if fetch_one:
            return cur.fetchone()
        else:
            return cur.fetchall()
