#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Neon database schema and migrate data from local database
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Neon database URL
NEON_URL = os.environ.get("DATABASE_URL")
if not NEON_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    exit(1)

# Local database connection
LOCAL_CONN_STRING = "postgresql://sandwich:sandwich@localhost:5433/sandwich"

print("Sandy Data Migration - Schema Fix + Data Import")
print("=" * 60)

# Step 1: Fix Neon schema
print("\n Step 1: Fixing Neon schema...")
try:
    neon_conn = psycopg2.connect(NEON_URL, connect_timeout=10)
    neon_conn.autocommit = True
    cur = neon_conn.cursor()

    # Set statement timeout to prevent hanging
    cur.execute("SET statement_timeout = '30s'")

    # Check if column exists
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'sandwiches'
        AND column_name IN ('reuben_commentary', 'sandy_commentary')
    """)

    existing_cols = [row[0] for row in cur.fetchall()]
    print(f"   Found columns: {existing_cols}")

    if 'sandy_commentary' in existing_cols:
        print("   OK Schema already has sandy_commentary")
    else:
        print("   Need to recreate schema with sandy_commentary...")

        # Terminate other connections to avoid locks
        print("   Terminating other connections...")
        cur.execute("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = current_database()
            AND pid <> pg_backend_pid()
        """)

        # Read and execute init_schema.sql
        with open('src/sandwich/db/init_schema.sql', 'r') as f:
            schema_sql = f.read()

        # Drop existing tables
        print("   Dropping existing tables...")
        cur.execute("DROP TABLE IF EXISTS sandwiches CASCADE")
        cur.execute("DROP TABLE IF EXISTS sources CASCADE")
        cur.execute("DROP TABLE IF EXISTS structural_types CASCADE")

        # Create fresh schema
        print("   Creating fresh schema...")
        cur.execute(schema_sql)
        print("   OK Schema created")

    cur.close()
    neon_conn.close()

except Exception as e:
    print(f"X Schema fix failed: {e}")
    exit(1)

# Step 2: Migrate data
print("\n Step 2: Migrating data from local database...")
try:
    local_conn = psycopg2.connect(LOCAL_CONN_STRING)
    neon_conn = psycopg2.connect(NEON_URL)

    local_cur = local_conn.cursor(cursor_factory=RealDictCursor)
    neon_cur = neon_conn.cursor()

    # Backup human ratings before clearing data (they only exist in Neon, not local)
    print("   Backing up human ratings...")
    neon_cur.execute("SELECT * FROM human_ratings")
    human_ratings_backup = neon_cur.fetchall()
    print(f"   Backed up {len(human_ratings_backup)} human ratings")

    # Delete in correct order (respecting foreign keys)
    print("   Clearing existing data...")
    neon_cur.execute("DELETE FROM sandwiches")
    neon_cur.execute("DELETE FROM sources")
    neon_cur.execute("DELETE FROM structural_types")

    # Migrate structural_types
    print("   Copying structural_types...")
    local_cur.execute("SELECT type_id, name, description FROM structural_types ORDER BY type_id")
    types = local_cur.fetchall()

    for t in types:
        neon_cur.execute(
            "INSERT INTO structural_types (type_id, name, description) VALUES (%s, %s, %s) ON CONFLICT (type_id) DO NOTHING",
            (t['type_id'], t['name'], t['description'])
        )
    print(f"   OK Copied {len(types)} structural types")

    # Migrate sources
    print("   Copying sources...")
    local_cur.execute("SELECT source_id, url, fetched_at FROM sources ORDER BY source_id")
    sources = local_cur.fetchall()

    for s in sources:
        neon_cur.execute(
            "INSERT INTO sources (source_id, url, fetched_at) VALUES (%s, %s, %s) ON CONFLICT (source_id) DO NOTHING",
            (s['source_id'], s['url'], s['fetched_at'])
        )
    print(f"   OK Copied {len(sources)} sources")

    # Migrate sandwiches
    print("   Copying sandwiches...")
    local_cur.execute("""
        SELECT sandwich_id, name, description, source_id, structural_type_id,
               assembly_rationale, sandy_commentary, specificity_score,
               validity_score, bread_compat_score, containment_score,
               nontrivial_score, novelty_score,
               created_at, sandwich_embedding, bread_top, bread_bottom, filling
        FROM sandwiches ORDER BY created_at
    """)
    sandwiches = local_cur.fetchall()

    neon_cur.execute("DELETE FROM sandwiches")

    for sw in sandwiches:
        neon_cur.execute("""
            INSERT INTO sandwiches (
                sandwich_id, name, description, source_id, structural_type_id,
                assembly_rationale, sandy_commentary, specificity_score,
                validity_score, bread_compat_score, containment_score,
                nontrivial_score, novelty_score,
                created_at, sandwich_embedding, bread_top, bread_bottom, filling
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (sandwich_id) DO NOTHING
        """, (
            sw['sandwich_id'], sw['name'], sw['description'], sw['source_id'],
            sw['structural_type_id'], sw['assembly_rationale'],
            sw['sandy_commentary'], sw['specificity_score'],
            sw['validity_score'], sw['bread_compat_score'], sw['containment_score'],
            sw['nontrivial_score'], sw['novelty_score'],
            sw['created_at'], sw['sandwich_embedding'],
            sw['bread_top'], sw['bread_bottom'], sw['filling']
        ))

    print(f"   OK Copied {len(sandwiches)} sandwiches")

    # Restore human ratings
    print("   Restoring human ratings...")
    ratings_restored = 0
    ratings_orphaned = 0

    if human_ratings_backup:
        # Get list of valid sandwich IDs
        neon_cur.execute("SELECT sandwich_id FROM sandwiches")
        valid_sandwich_ids = {row[0] for row in neon_cur.fetchall()}

        for rating in human_ratings_backup:
            # Only restore if the sandwich still exists
            if rating[1] in valid_sandwich_ids:  # rating[1] is sandwich_id
                neon_cur.execute("""
                    INSERT INTO human_ratings (
                        rating_id, sandwich_id, session_id, bread_compat_score,
                        containment_score, nontrivial_score, novelty_score,
                        overall_validity, created_at, user_agent, ip_hash
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (rating_id) DO NOTHING
                """, rating)
                ratings_restored += 1
            else:
                ratings_orphaned += 1

        print(f"   OK Restored {ratings_restored} human ratings")
        if ratings_orphaned > 0:
            print(f"   WARNING: {ratings_orphaned} ratings skipped (sandwiches no longer exist)")

    neon_conn.commit()

    # Verify
    neon_cur.execute("SELECT COUNT(*) FROM sandwiches")
    count = neon_cur.fetchone()[0]
    neon_cur.execute("SELECT COUNT(*) FROM human_ratings")
    ratings_count = neon_cur.fetchone()[0]
    print(f"\nOK Migration verified: {count} sandwiches, {ratings_count} human ratings in Neon")

    local_cur.close()
    local_conn.close()
    neon_cur.close()
    neon_conn.close()

    print("\n Migration complete!")
    print(f"\nYour {count} sandwiches are now in the cloud database.")
    print("Push to GitHub to update the Streamlit dashboard.")

except Exception as e:
    print(f"X Data migration failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
