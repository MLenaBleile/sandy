# Dashboard Improvement Prompts

**Purpose:** Comprehensive prompting suite for upgrading the Sandy dashboard from a reporting tool to a research-grade analytics platform with human-in-the-loop evaluation.

**Context:** The dashboard is built with Streamlit, connects to PostgreSQL + pgvector (Neon cloud), and is deployed on Streamlit Cloud

**Reference Documents:**
- `DASHBOARD_IMPROVEMENT_PLAN.md` - Complete improvement roadmap
- `SPEC.md` Section 14 - Original dashboard specification
- Critical review findings (embedded in improvement plan)

---

## Execution Strategy

**IMPORTANT:** These prompts should be executed in order. Each prompt builds on the previous work and assumes prior steps are complete.

**Before starting:**
1. Read `DASHBOARD_IMPROVEMENT_PLAN.md` to understand the full scope
2. Ensure local Docker database is running: `docker compose up db -d`
3. Have access to Neon database credentials for testing
4. Backup current dashboard code: `git checkout -b dashboard-improvements`

**Testing between prompts:**
- Test locally: `docker compose up dashboard -d` then visit http://localhost:8501
- Test migrations on Neon before deploying to Streamlit Cloud
- Verify no regressions on existing features

---

## Prompt 14: Database Schema Enhancement & Performance Indexes

**Objective:** Add database indexes, human ratings table, materialized views, and connection pooling for 10-100x performance improvement.

**Prerequisites:**
- PostgreSQL database is running (local or Neon)
- You have `src/sandwich/db/init_schema.sql` available
- Current schema version is known

**Files to create/modify:**
- `src/sandwich/db/migrations/001_performance_indexes.sql` (new)
- `src/sandwich/db/migrations/002_human_ratings.sql` (new)
- `src/sandwich/db/migrations/003_materialized_views.sql` (new)
- `dashboard/utils/db.py` (modify - add connection pooling)
- `scripts/migrate_db.py` (new - migration runner)

**Requirements:**

### 1. Performance Indexes

Create migration file `src/sandwich/db/migrations/001_performance_indexes.sql` with:

```sql
-- Migration: Performance Indexes
-- Purpose: Speed up dashboard queries 10-100x
-- Date: 2024-02-XX

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
```

### 2. Human Ratings Table

Create migration file `src/sandwich/db/migrations/002_human_ratings.sql`:

```sql
-- Migration: Human Ratings System
-- Purpose: Enable visitor feedback on sandwich quality
-- Date: 2024-02-XX

CREATE TABLE IF NOT EXISTS human_ratings (
    rating_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sandwich_id UUID NOT NULL REFERENCES sandwiches(sandwich_id) ON DELETE CASCADE,
    session_id UUID NOT NULL,

    -- Component scores (matching Reuben's dimensions)
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
CREATE INDEX idx_ratings_sandwich ON human_ratings(sandwich_id);
CREATE INDEX idx_ratings_session ON human_ratings(session_id);
CREATE INDEX idx_ratings_created ON human_ratings(created_at DESC);

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
```

### 3. Materialized Views

Create migration file `src/sandwich/db/migrations/003_materialized_views.sql`:

```sql
-- Migration: Materialized Views for Analytics
-- Purpose: Pre-compute expensive aggregations
-- Date: 2024-02-XX

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

CREATE INDEX idx_mv_type_stats ON mv_structural_type_stats(structural_type, domain);

-- View: Daily statistics (already exists in init_schema.sql but ensure it's current)
REFRESH MATERIALIZED VIEW IF EXISTS daily_stats;

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_structural_type_stats;
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_stats;
END;
$$ LANGUAGE plpgsql;

-- Initial refresh
SELECT refresh_all_materialized_views();
```

### 4. Connection Pooling

Update `dashboard/utils/db.py` to use connection pooling:

```python
"""Database connection utilities with connection pooling."""

import os
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
import streamlit as st
import logging
import hashlib

logger = logging.getLogger(__name__)

# Global connection pool
_pool = None


@st.cache_resource
def get_db_pool():
    """Get or create a cached connection pool.

    Uses ThreadedConnectionPool for efficient connection reuse.
    Pool is shared across all users/sessions in Streamlit Cloud.
    """
    global _pool

    if _pool is not None:
        return _pool

    # Try to get DATABASE_URL from env or Streamlit secrets
    database_url = os.getenv('DATABASE_URL')

    if database_url is None and hasattr(st, 'secrets') and 'DATABASE_URL' in st.secrets:
        database_url = st.secrets['DATABASE_URL']

    if database_url is None:
        raise ValueError(
            "DATABASE_URL not found. Set environment variable or add to Streamlit secrets."
        )

    logger.info("Creating connection pool...")

    # Create pool with 1-10 connections
    _pool = ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        dsn=database_url,
        cursor_factory=RealDictCursor
    )

    # Register UUID adapter
    psycopg2.extras.register_uuid()

    logger.info("Connection pool created successfully")

    return _pool


def get_db_connection():
    """Get a connection from the pool.

    IMPORTANT: Caller must return connection via return_db_connection()
    or use in a try/finally block.

    Returns:
        psycopg2 connection with RealDictCursor
    """
    pool = get_db_pool()
    conn = pool.getconn()
    return conn


def return_db_connection(conn):
    """Return a connection to the pool.

    Args:
        conn: Connection to return
    """
    if conn is None:
        return

    pool = get_db_pool()
    pool.putconn(conn)


def check_database_connection() -> bool:
    """Check if database connection is healthy.

    Returns:
        True if connection is working, False otherwise
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
        return result is not None
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        import sys
        print(f"DB Connection Error: {type(e).__name__}: {e}", file=sys.stderr)
        return False
    finally:
        if conn:
            return_db_connection(conn)


def execute_query(query: str, params: tuple = None, fetch_one: bool = False):
    """Execute a query and return results with proper connection handling.

    Args:
        query: SQL query string
        params: Query parameters (for parameterized queries)
        fetch_one: If True, return single row instead of list

    Returns:
        Single dict if fetch_one=True, otherwise list of dicts

    Raises:
        Exception: If query execution fails
    """
    conn = None
    try:
        conn = get_db_connection()

        with conn.cursor() as cur:
            cur.execute(query, params or ())

            if fetch_one:
                return cur.fetchone()
            else:
                return cur.fetchall()

    except Exception as e:
        logger.error(f"Query failed: {query[:100]}... Error: {e}")
        raise

    finally:
        if conn:
            return_db_connection(conn)


def hash_ip(ip_address: str) -> str:
    """Hash IP address for privacy-preserving spam prevention.

    Args:
        ip_address: Client IP address

    Returns:
        SHA256 hash of IP address
    """
    return hashlib.sha256(ip_address.encode()).hexdigest()
```

### 5. Migration Runner Script

Create `scripts/migrate_db.py`:

```python
"""Database migration runner.

Applies SQL migrations in order from src/sandwich/db/migrations/
"""

import os
import sys
from pathlib import Path
import psycopg2
from psycopg2 import sql

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def get_database_url() -> str:
    """Get database URL from environment."""
    db_url = os.getenv('DATABASE_URL') or os.getenv('SANDWICH_DATABASE__URL')

    if not db_url:
        raise ValueError(
            "DATABASE_URL not set. Use: export DATABASE_URL='postgresql://...'"
        )

    return db_url


def create_migrations_table(conn):
    """Create migrations tracking table."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                migration_name VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT NOW()
            )
        """)
    conn.commit()


def get_applied_migrations(conn) -> set:
    """Get set of already-applied migration names."""
    with conn.cursor() as cur:
        cur.execute("SELECT migration_name FROM schema_migrations")
        return {row[0] for row in cur.fetchall()}


def apply_migration(conn, migration_path: Path):
    """Apply a single migration file."""
    migration_name = migration_path.name

    print(f"Applying migration: {migration_name}")

    with open(migration_path) as f:
        migration_sql = f.read()

    with conn.cursor() as cur:
        # Execute migration
        cur.execute(migration_sql)

        # Record migration
        cur.execute(
            "INSERT INTO schema_migrations (migration_name) VALUES (%s)",
            (migration_name,)
        )

    conn.commit()
    print(f"✓ Applied: {migration_name}")


def run_migrations(dry_run: bool = False):
    """Run all pending migrations."""
    migrations_dir = project_root / "src" / "sandwich" / "db" / "migrations"

    if not migrations_dir.exists():
        print(f"Creating migrations directory: {migrations_dir}")
        migrations_dir.mkdir(parents=True, exist_ok=True)

    # Get all migration files (sorted)
    migration_files = sorted(migrations_dir.glob("*.sql"))

    if not migration_files:
        print("No migration files found.")
        return

    # Connect to database
    db_url = get_database_url()
    print(f"Connecting to database...")

    conn = psycopg2.connect(db_url)

    try:
        # Create migrations table
        create_migrations_table(conn)

        # Get already-applied migrations
        applied = get_applied_migrations(conn)
        print(f"Already applied: {len(applied)} migrations")

        # Apply pending migrations
        pending = [f for f in migration_files if f.name not in applied]

        if not pending:
            print("✓ All migrations up to date!")
            return

        print(f"\nPending migrations: {len(pending)}")
        for mig in pending:
            print(f"  - {mig.name}")

        if dry_run:
            print("\nDry run - no changes made.")
            return

        print("\nApplying migrations...")
        for migration_file in pending:
            apply_migration(conn, migration_file)

        print(f"\n✓ Successfully applied {len(pending)} migrations!")

    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Show pending migrations without applying"
    )

    args = parser.parse_args()

    run_migrations(dry_run=args.dry_run)
```

**Validation:**

After implementing:

1. **Test migrations locally:**
   ```bash
   # Dry run first
   python scripts/migrate_db.py --dry-run

   # Apply migrations
   export DATABASE_URL="postgresql://sandwich:sandwich@localhost:5433/sandwich"
   python scripts/migrate_db.py
   ```

2. **Test migrations on Neon:**
   ```bash
   export DATABASE_URL="your-neon-url-here"
   python scripts/migrate_db.py
   ```

3. **Verify indexes were created:**
   ```sql
   SELECT indexname, indexdef
   FROM pg_indexes
   WHERE tablename = 'sandwiches';
   ```

4. **Test connection pooling:**
   ```bash
   # Start dashboard
   docker compose up dashboard -d

   # Check logs for "Connection pool created"
   docker compose logs dashboard | grep -i pool
   ```

5. **Benchmark query performance:**
   ```sql
   -- Before indexes (baseline)
   EXPLAIN ANALYZE SELECT * FROM sandwiches ORDER BY created_at DESC LIMIT 20;

   -- After indexes (should show Index Scan, much faster)
   EXPLAIN ANALYZE SELECT * FROM sandwiches ORDER BY created_at DESC LIMIT 20;
   ```

**Success criteria:**
- ✅ All 3 migration files created
- ✅ Migrations apply cleanly on local and Neon databases
- ✅ 8 new indexes created on `sandwiches` table
- ✅ `human_ratings` table exists with proper constraints
- ✅ Materialized views created and populated
- ✅ Connection pooling implemented in `db.py`
- ✅ Migration runner script works with `--dry-run` flag
- ✅ Query performance improved (verify with EXPLAIN ANALYZE)
- ✅ No errors in dashboard when connecting with pooled connections

---

## Prompt 15: Human Rating Widget Component

**Objective:** Create interactive rating widget that allows visitors to rate sandwiches and see real-time comparison with Reuben's scores.

**Prerequisites:**
- Prompt 14 completed (human_ratings table exists)
- Database connection pooling is working
- Streamlit dashboard runs locally

**Files to create:**
- `dashboard/components/rating_widget.py` (new)
- `dashboard/utils/ratings.py` (new - backend logic)

**Files to modify:**
- `dashboard/components/sandwich_card.py` (add rating integration)
- `dashboard/utils/queries.py` (add rating queries)

**Requirements:**

### 1. Rating Backend Logic

Create `dashboard/utils/ratings.py`:

```python
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
```

### 2. Rating Widget Component

Create `dashboard/components/rating_widget.py`:

```python
"""Interactive rating widget for human evaluation of sandwiches."""

import streamlit as st
from typing import Dict, Any

from dashboard.utils.ratings import (
    get_or_create_session_id,
    check_rate_limit,
    has_rated_sandwich,
    save_rating,
    get_human_consensus
)


def rating_widget(
    sandwich: Dict[str, Any],
    show_comparison: bool = True,
    expanded: bool = False
) -> None:
    """Render interactive rating widget for a sandwich.

    Allows users to rate sandwiches on 4 component dimensions + overall.
    Shows real-time comparison between user rating and Reuben's self-assessment.

    Args:
        sandwich: Dictionary containing sandwich data
        show_comparison: If True, show Reuben vs Human comparison after rating
        expanded: If True, expand rating form by default
    """
    sandwich_id = sandwich.get('sandwich_id')

    if not sandwich_id:
        st.warning("Cannot rate sandwich: missing ID")
        return

    session_id = get_or_create_session_id()

    # Check if already rated
    already_rated = has_rated_sandwich(session_id, sandwich_id)

    if already_rated:
        st.info("✅ You've already rated this sandwich! Thanks for your feedback.")

        if show_comparison:
            show_rating_comparison(sandwich)

        return

    # Check rate limit
    is_within_limit, ratings_used = check_rate_limit(session_id, max_ratings=10, window_hours=1)

    if not is_within_limit:
        st.warning(f"⏳ You've reached the rating limit ({ratings_used}/10 per hour). Please try again later.")
        return

    # Show remaining ratings
    remaining = 10 - ratings_used
    st.caption(f"💡 You can submit {remaining} more ratings this hour")

    # Rating form
    with st.expander("🎯 Rate This Sandwich", expanded=expanded):
        st.markdown("""
        Help validate Reuben's self-assessment! Rate each dimension honestly.
        Your ratings are anonymous and help improve the system.
        """)

        with st.form(key=f"rating_form_{sandwich_id}"):
            # Bread Compatibility
            st.markdown("### 🍞 Bread Compatibility")
            st.caption("Are both breads the same type of thing? Do they relate independently of the filling?")
            bread_compat = st.slider(
                "Bread Compatibility Score",
                0.0, 1.0, 0.5, 0.05,
                help="1.0 = Perfect bread pairing, 0.0 = Unrelated breads",
                key=f"bread_{sandwich_id}",
                label_visibility="collapsed"
            )

            # Containment
            st.markdown("### 📦 Containment")
            st.caption("Does the filling genuinely emerge from the space between the breads?")
            containment = st.slider(
                "Containment Score",
                0.0, 1.0, 0.5, 0.05,
                help="1.0 = Filling perfectly bounded, 0.0 = No containment",
                key=f"contain_{sandwich_id}",
                label_visibility="collapsed"
            )

            # Non-triviality / Specificity
            st.markdown("### ✨ Specificity")
            st.caption("Are ingredients concrete and specific, not vague abstractions?")
            nontrivial = st.slider(
                "Specificity Score",
                0.0, 1.0, 0.5, 0.05,
                help="1.0 = Highly specific, 0.0 = Vague/abstract",
                key=f"nontrivial_{sandwich_id}",
                label_visibility="collapsed"
            )

            # Novelty
            st.markdown("### 🌟 Novelty")
            st.caption("How original is this sandwich compared to others you've seen?")
            novelty = st.slider(
                "Novelty Score",
                0.0, 1.0, 0.5, 0.05,
                help="1.0 = Completely novel, 0.0 = Derivative",
                key=f"novelty_{sandwich_id}",
                label_visibility="collapsed"
            )

            # Overall validity
            st.markdown("### ⭐ Overall Validity")
            st.caption("Considering everything, is this a valid sandwich?")
            overall = st.slider(
                "Overall Validity Score",
                0.0, 1.0, 0.5, 0.05,
                help="1.0 = Excellent sandwich, 0.0 = Not a sandwich",
                key=f"overall_{sandwich_id}",
                label_visibility="collapsed"
            )

            # Submit button
            col1, col2 = st.columns([1, 3])
            with col1:
                submitted = st.form_submit_button(
                    "Submit Rating",
                    type="primary",
                    use_container_width=True
                )
            with col2:
                if submitted:
                    st.caption("Submitting...")

            if submitted:
                scores = {
                    'bread_compat': bread_compat,
                    'containment': containment,
                    'nontrivial': nontrivial,
                    'novelty': novelty,
                    'overall': overall
                }

                success = save_rating(sandwich_id, session_id, scores)

                if success:
                    st.success("🎉 Rating saved! Thank you for helping validate Reuben's work.")
                    st.rerun()
                else:
                    st.error("Failed to save rating. Please try again.")


def show_rating_comparison(sandwich: Dict[str, Any]) -> None:
    """Display comparison between Reuben's scores and human consensus.

    Args:
        sandwich: Dictionary containing sandwich data with Reuben's scores
    """
    sandwich_id = sandwich.get('sandwich_id')

    if not sandwich_id:
        return

    human_stats = get_human_consensus(sandwich_id)

    if not human_stats or human_stats['rating_count'] == 0:
        st.info("Be the first to rate this sandwich!")
        return

    st.markdown("### 🤖 vs 👥 Comparison")

    rating_count = human_stats['rating_count']

    # Overall comparison
    col1, col2, col3 = st.columns(3)

    with col1:
        reuben_overall = sandwich.get('validity_score', 0)
        st.metric("🤖 Reuben's Score", f"{reuben_overall:.2f}")

    with col2:
        human_overall = human_stats.get('avg_overall', 0) or 0
        st.metric(
            f"👥 Human Consensus",
            f"{human_overall:.2f}",
            help=f"Based on {rating_count} rating(s)"
        )

    with col3:
        delta = human_overall - reuben_overall
        agreement_color = "normal" if abs(delta) < 0.2 else "inverse"
        st.metric(
            "Agreement",
            f"{delta:+.2f}",
            delta_color=agreement_color
        )

    st.caption(f"📊 Based on {rating_count} human rating(s)")

    # Component breakdown
    st.markdown("**Component Comparison:**")

    components = [
        ('🍞 Bread Compat', 'bread_compat_score', 'avg_bread_compat'),
        ('📦 Containment', 'containment_score', 'avg_containment'),
        ('✨ Specificity', 'nontrivial_score', 'avg_nontrivial'),
        ('🌟 Novelty', 'novelty_score', 'avg_novelty')
    ]

    for label, reuben_key, human_key in components:
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.write(f"**{label}:**")

        with col2:
            reuben_val = sandwich.get(reuben_key, 0) or 0
            st.write(f"🤖 {reuben_val:.2f}")

        with col3:
            human_val = human_stats.get(human_key, 0) or 0
            delta = human_val - reuben_val
            color = "🟢" if abs(delta) < 0.15 else "🟡" if abs(delta) < 0.3 else "🔴"
            st.write(f"👥 {human_val:.2f} {color}")
```

### 3. Integration into Sandwich Card

Update `dashboard/components/sandwich_card.py` to include rating widget:

```python
# Add import at top
from dashboard.components.rating_widget import rating_widget

# Modify sandwich_card function signature
def sandwich_card(
    sandwich: Dict[str, Any],
    expanded: bool = False,
    enable_rating: bool = False  # New parameter
):
    """Render a sandwich card using only Streamlit native components with cute styling.

    Args:
        sandwich: Dictionary containing sandwich data
        expanded: If True, show full details by default
        enable_rating: If True, show rating widget
    """
    # ... existing card display code ...

    # At the end, before st.markdown("---"):

    # Add rating widget if enabled
    if enable_rating:
        st.markdown("---")
        rating_widget(sandwich, show_comparison=True, expanded=False)

    st.markdown("---")
```

### 4. Add Rating Queries

Update `dashboard/utils/queries.py` to add rating-related queries:

```python
# Add at end of file

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
```

**Validation:**

After implementing:

1. **Test rating submission:**
   - Visit Live Feed or Browser page
   - Submit a rating for a sandwich
   - Verify rating appears in database:
     ```sql
     SELECT * FROM human_ratings ORDER BY created_at DESC LIMIT 5;
     ```

2. **Test rate limiting:**
   - Submit 10 ratings rapidly
   - Verify 11th rating is blocked with appropriate message

3. **Test duplicate prevention:**
   - Rate a sandwich
   - Refresh page
   - Verify you see "already rated" message instead of form

4. **Test comparison display:**
   - Rate a sandwich with intentionally different scores
   - Verify Reuben vs Human comparison shows correctly
   - Check delta calculation is accurate

5. **Test session persistence:**
   - Rate a sandwich
   - Navigate to different page
   - Return to same sandwich
   - Verify still shows "already rated"

**Success criteria:**
- ✅ Rating widget renders with 5 sliders
- ✅ Submissions save to `human_ratings` table
- ✅ Rate limiting prevents spam (10/hour)
- ✅ Duplicate ratings blocked per session
- ✅ Comparison shows Reuben vs Human scores
- ✅ Component-level comparison displays correctly
- ✅ Session ID persists across page navigation
- ✅ Rating count displays accurately
- ✅ Visual indicators (🟢🟡🔴) show agreement level
- ✅ Error handling prevents crashes on DB failures

---

## Prompt 16: Human Ratings Analytics Page

**Objective:** Create comprehensive analytics page showing Reuben vs Human consensus analysis, calibration metrics, and research-grade insights.

**Prerequisites:**
- Prompt 14 completed (database schema)
- Prompt 15 completed (rating widget)
- Some human ratings collected (at least 10-20 for meaningful analysis)

**Files to create:**
- `pages/7_👥_Human_Ratings.py` (new page)

**Files to modify:**
- `dashboard/utils/queries.py` (add advanced rating analytics queries)

**Requirements:**

### Page Structure

The Human Ratings page should have these sections:

1. **Overview Metrics** - Total ratings, sandwiches rated, unique raters, average agreement
2. **Calibration Analysis** - Scatter plot of Reuben vs Human scores with correlation
3. **Biggest Disagreements** - Top 10 sandwiches where Reuben and humans diverge most
4. **Component-Level Analysis** - Which dimensions have highest/lowest agreement
5. **Inter-Rater Reliability** - Statistical measures of human agreement
6. **Temporal Trends** - How agreement changes over time
7. **Export Section** - Download rating data for research

### Implementation

Create `pages/7_👥_Human_Ratings.py`:

(Due to length, I'll provide the complete implementation in the actual file creation. Key features include:)

- Scipy statistical tests (Pearson correlation, t-tests)
- Plotly interactive scatter plots with trend lines
- Component-level bar charts
- Temporal line charts showing drift
- Research-grade statistics (Cronbach's alpha, ICC)
- Data export for external analysis

**Validation:**

1. Test with minimal data (< 10 ratings)
2. Test with moderate data (50-100 ratings)
3. Verify statistical calculations are correct
4. Check all charts render properly
5. Test export functionality

**Success criteria:**
- ✅ Page loads without human ratings (shows helpful empty state)
- ✅ Correlation coefficient calculated correctly
- ✅ Scatter plot shows diagonal reference line
- ✅ Biggest disagreements ordered correctly
- ✅ Component analysis uses proper averaging
- ✅ Statistical tests run without errors
- ✅ Export downloads valid CSV/JSON
- ✅ Page responsive on mobile

---

## Prompt 17: Statistical Enhancements to Analytics Page

**Objective:** Upgrade existing Analytics page with statistical rigor: confidence intervals, significance tests, correlation matrices, box plots.

**Prerequisites:**
- Analytics page exists (`pages/3_📈_Analytics.py`)
- Sufficient sandwich data (recommend 50+ sandwiches)

**Files to modify:**
- `pages/3_📈_Analytics.py`

**Requirements:**

### Enhancements to Add

1. **Validity Distribution** - Add mean/median lines, std dev bands, normality test
2. **Correlation Matrix** - Show component score correlations with heatmap
3. **Box Plots by Type** - Compare validity distributions with ANOVA test
4. **Time Series** - Add trend line and confidence bands to sandwich creation chart
5. **Anomaly Detection** - Flag statistical outliers using Z-scores
6. **Component Score Analysis** - Replace radar chart with parallel coordinates

### Statistical Tests to Include

- Shapiro-Wilk test for normality
- ANOVA for multi-group comparison
- Post-hoc tests (Tukey HSD) if ANOVA significant
- Pearson/Spearman correlation
- Outlier detection (Z-score, IQR method)

**Validation:**

Test with:
- Small dataset (< 10 sandwiches)
- Medium dataset (50-100)
- Large dataset (500+)
- Edge cases (all same type, extreme outliers)

**Success criteria:**
- ✅ Statistical overlays don't break on small datasets
- ✅ P-values calculated correctly
- ✅ Charts remain readable with annotations
- ✅ Performance acceptable (< 2s render time)
- ✅ Export includes statistical summary

---

## Prompt 18: Network Graph Visualization

**Objective:** Create interactive network graph showing sandwich relationships based on similarity scores from embeddings.

**Prerequisites:**
- Sandwich relations data exists in database
- NetworkX and Plotly installed

**Files to create:**
- `pages/4_🗺️_Network.py` (replaces removed Exploration page)

**Requirements:**

- Interactive force-directed graph
- Node sizing by validity score
- Edge width by similarity
- Community detection (Louvain algorithm)
- Centrality metrics (degree, betweenness, PageRank)
- Filtering by similarity threshold
- Click node to see sandwich details

**Validation:**

- Test with no edges (low similarity threshold)
- Test with dense graph (high node/edge count)
- Verify graph layout is stable
- Check performance with 100+ nodes

**Success criteria:**
- ✅ Graph renders in < 5 seconds
- ✅ Interactive hover shows sandwich names
- ✅ Community colors help identify clusters
- ✅ Centrality metrics accurate
- ✅ Responsive zoom/pan

---

## Prompt 19: Anomaly Detection & Alerts

**Objective:** Add anomaly detection to flag unusual sandwiches, quality degradation, or data issues.

**Files to modify:**
- `pages/3_📈_Analytics.py` (add Anomaly Detection section)

**Requirements:**

- Z-score based outlier detection (|z| > 2.5)
- Isolation Forest for multivariate anomalies
- Temporal anomaly detection (unusual creation rate spikes)
- Quality drift detection (rolling average trends)
- Visual highlighting of outliers

**Success criteria:**
- ✅ Correctly identifies statistical outliers
- ✅ No false positives on normal variation
- ✅ Clear explanation of why flagged

---

## Prompt 20: Full-Text Search Upgrade

**Objective:** Replace inefficient ILIKE queries with PostgreSQL full-text search for better performance and relevance.

**Files to modify:**
- `src/sandwich/db/migrations/004_fulltext_search.sql` (new migration)
- `dashboard/utils/queries.py` (update search_sandwiches function)

**Requirements:**

- Add tsvector column to sandwiches table
- Create GIN index on tsvector
- Update trigger to maintain search_vector
- Replace ILIKE with @@ operator
- Add ranking by relevance

**Success criteria:**
- ✅ Search 10x faster on 1000+ sandwiches
- ✅ Relevance ranking works
- ✅ Backward compatible (old searches still work)

---

## Prompt 21: Testing & Documentation

**Objective:** Add comprehensive tests and update documentation for new dashboard features.

**Files to create:**
- `tests/dashboard/test_rating_widget.py`
- `tests/dashboard/test_ratings_backend.py`
- `tests/dashboard/test_analytics_stats.py`
- `docs/HUMAN_RATINGS.md` (research documentation)

**Files to update:**
- `README.md` (add Human Ratings section)
- `DEPLOYMENT.md` (migration instructions)

**Requirements:**

- Unit tests for rating backend (85%+ coverage)
- Integration tests for rating submission flow
- Statistical test validation (check calculation accuracy)
- Documentation for researchers using rating data

**Success criteria:**
- ✅ 90%+ test coverage on new code
- ✅ All tests pass on CI
- ✅ Documentation clear and comprehensive

---

## Prompt 22: Deployment & Monitoring

**Objective:** Deploy improved dashboard to Streamlit Cloud and set up monitoring.

**Files to create:**
- `.github/workflows/dashboard-deploy.yml` (optional CI/CD)
- `scripts/health_check.py` (monitoring script)

**Tasks:**

1. Run all migrations on Neon production database
2. Deploy to Streamlit Cloud
3. Test all features in production
4. Monitor error rates and performance
5. Set up analytics tracking (optional)

**Validation:**

- [ ] All migrations applied successfully
- [ ] No errors in Streamlit Cloud logs
- [ ] Human rating submissions working
- [ ] Performance acceptable (< 3s page load)
- [ ] Mobile responsive
- [ ] Database query performance good

**Success criteria:**
- ✅ Dashboard live at https://reuben.streamlit.app
- ✅ All pages load without errors
- ✅ Human ratings saving to database
- ✅ Analytics showing current data
- ✅ No performance regressions

---

## Execution Notes

### Recommended Order

**Week 1: Foundation**
1. Prompt 14 (Database schema) - Monday
2. Prompt 15 (Rating widget) - Tuesday-Wednesday
3. Prompt 16 (Ratings analytics) - Thursday-Friday

**Week 2: Analytics Depth**
4. Prompt 17 (Statistical enhancements) - Monday-Tuesday
5. Prompt 18 (Network graph) - Wednesday-Thursday
6. Prompt 19 (Anomaly detection) - Friday

**Week 3: Polish & Deploy**
7. Prompt 20 (Full-text search) - Monday
8. Prompt 21 (Testing) - Tuesday-Thursday
9. Prompt 22 (Deployment) - Friday

### Testing Strategy

After each prompt:
1. Test locally with Docker
2. Test on Neon staging database
3. Run existing tests (ensure no regressions)
4. Manual QA on key user flows
5. Commit to feature branch

After all prompts:
1. Full integration testing
2. Performance testing with load
3. Security review (SQL injection, rate limiting)
4. Deploy to production

### Rollback Plan

If deployment fails:
1. Revert Streamlit Cloud to previous commit
2. Keep Neon database (migrations are additive)
3. Fix issues locally
4. Re-deploy when stable

### Success Metrics

After full implementation:

**Performance:**
- [ ] 95th percentile query time < 500ms
- [ ] Page load time < 3s
- [ ] 100 concurrent users supported

**Features:**
- [ ] Human ratings: 100+ total ratings
- [ ] Analytics: All statistical tests working
- [ ] Network: Graph renders with 200+ nodes
- [ ] Search: Full-text search 10x faster

**Quality:**
- [ ] 90%+ test coverage
- [ ] Zero critical bugs
- [ ] Mobile responsive
- [ ] Accessible (WCAG AA)

---

## Additional Resources

**Reference Materials:**
- Streamlit docs: https://docs.streamlit.io
- Plotly Python: https://plotly.com/python/
- Scipy stats: https://docs.scipy.org/doc/scipy/reference/stats.html
- PostgreSQL full-text: https://www.postgresql.org/docs/current/textsearch.html

**Code Examples:**
- See `DASHBOARD_IMPROVEMENT_PLAN.md` for detailed implementations
- Original dashboard code in `dashboard/` directory
- Database schema in `src/sandwich/db/init_schema.sql`

**Getting Help:**
- Check Streamlit community forum
- Review PostgreSQL query plans with EXPLAIN ANALYZE
- Test statistical calculations with known datasets
- Validate against original dashboard behavior

---

**End of Dashboard Prompting Suite**

Total estimated time: 80-100 hours over 3-4 weeks
Priority: High-impact features first (database, ratings, statistics)
Deployment: Incremental (test locally, staging, then production)
