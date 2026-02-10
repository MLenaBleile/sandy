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
