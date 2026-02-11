#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Neon database transaction issues
"""
import os
import sys
import psycopg2

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Neon database URL
NEON_URL = os.environ.get("DATABASE_URL")
if not NEON_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    exit(1)

print("Fixing Neon database transaction issues...")

try:
    # Connect and terminate all other connections
    conn = psycopg2.connect(NEON_URL, connect_timeout=10)
    conn.autocommit = True
    cur = conn.cursor()

    # Terminate all other connections to clear any stuck transactions
    print("Terminating stuck connections...")
    cur.execute("""
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = current_database()
        AND pid <> pg_backend_pid()
        AND state IN ('idle in transaction', 'idle in transaction (aborted)')
    """)

    terminated = cur.fetchall()
    print(f"Terminated {len(terminated)} stuck connections")

    # Verify sandwiches table is accessible
    print("\nVerifying database...")
    cur.execute("SELECT COUNT(*) FROM sandwiches")
    count = cur.fetchone()[0]
    print(f"OK - Found {count} sandwiches in database")

    cur.execute("SELECT COUNT(*) FROM structural_types")
    types_count = cur.fetchone()[0]
    print(f"OK - Found {types_count} structural types")

    cur.close()
    conn.close()

    print("\nDatabase is healthy and ready!")

except Exception as e:
    print(f"X Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
