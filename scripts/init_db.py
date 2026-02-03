#!/usr/bin/env python3
"""Initialize the SANDWICH database schema.

Usage:
    docker-compose up -d
    python scripts/init_db.py
"""

import os
import sys
from pathlib import Path

import psycopg2

DATABASE_URL = os.environ.get(
    "SANDWICH_DATABASE__URL",
    "postgresql://sandwich:sandwich@localhost:5433/sandwich",
)

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "src" / "sandwich" / "db" / "init_schema.sql"


def main():
    print(f"Connecting to database: {DATABASE_URL}")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True

    schema_sql = SCHEMA_PATH.read_text()

    with conn.cursor() as cur:
        cur.execute(schema_sql)

    print("Schema created successfully.")

    # Verify tables exist
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
            """
        )
        tables = [row[0] for row in cur.fetchall()]

    print(f"Tables created: {', '.join(tables)}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
