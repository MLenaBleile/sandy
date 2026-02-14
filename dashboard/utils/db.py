"""Database connection utilities for the dashboard.

Provides cached database connections for Streamlit dashboard using the same
connection pattern as the main application.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
import logging
import hashlib

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
    except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
        # Connection is dead, clear cache and try once more
        logger.warning(f"Connection dead, clearing cache: {e}")
        get_db_connection.clear()

        try:
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
            return result is not None
        except Exception as retry_error:
            logger.error(f"Database health check failed after retry: {retry_error}")
            import sys
            print(f"DB Connection Error: {type(retry_error).__name__}: {retry_error}", file=sys.stderr)
            return False

    except Exception as e:
        # Log the full error for debugging
        logger.error(f"Database health check failed: {e}")
        # Also write to stderr for Streamlit logs
        import sys
        print(f"DB Connection Error: {type(e).__name__}: {e}", file=sys.stderr)
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
    max_retries = 2
    last_error = None

    # Detect if this is a write operation that needs a commit
    trimmed = query.strip().upper()
    is_write = trimmed.startswith(("INSERT", "UPDATE", "DELETE"))

    for attempt in range(max_retries):
        try:
            conn = get_db_connection()

            # Test if connection is still alive
            with conn.cursor() as test_cur:
                test_cur.execute("SELECT 1")

            # If alive, execute the actual query
            with conn.cursor() as cur:
                cur.execute(query, params or ())

                if is_write:
                    # Grab results before committing (if query returns rows)
                    result = None
                    if cur.description:
                        result = cur.fetchone() if fetch_one else cur.fetchall()
                    conn.commit()
                    return result if result is not None else []

                if fetch_one:
                    return cur.fetchone()
                else:
                    return cur.fetchall()

        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            # Connection is dead, clear the cache and retry
            logger.warning(f"Connection error (attempt {attempt + 1}/{max_retries}): {e}")
            last_error = e

            # Clear the cached connection
            get_db_connection.clear()

            if attempt < max_retries - 1:
                continue
            else:
                raise

        except Exception as e:
            logger.error(f"Query failed: {query[:100]}... Error: {e}")
            # Roll back failed write to keep connection usable
            try:
                conn = get_db_connection()
                conn.rollback()
            except Exception:
                pass
            raise

    # If we get here, all retries failed
    if last_error:
        raise last_error


def hash_ip(ip_address: str) -> str:
    """Hash IP address for privacy-preserving spam prevention.

    Args:
        ip_address: Client IP address

    Returns:
        SHA256 hash of IP address
    """
    return hashlib.sha256(ip_address.encode()).hexdigest()
