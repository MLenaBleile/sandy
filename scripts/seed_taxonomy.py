#!/usr/bin/env python3
"""Seed the structural_types table with the initial taxonomy from SPEC.md Section 4.2.

Usage:
    python scripts/seed_taxonomy.py
"""

import os
import sys

import psycopg2

DATABASE_URL = os.environ.get(
    "SANDWICH_DATABASE__URL",
    "postgresql://sandwich:sandwich@localhost:5432/sandwich",
)

# Initial taxonomy from SPEC.md Section 4.2
STRUCTURAL_TYPES = [
    {
        "name": "bound",
        "description": "Upper/lower limits bounding a quantity",
        "bread_relation": "Upper/lower limits",
        "filling_role": "Bounded quantity",
    },
    {
        "name": "dialectic",
        "description": "Thesis and antithesis framing a synthesis",
        "bread_relation": "Thesis/antithesis",
        "filling_role": "Synthesis",
    },
    {
        "name": "epistemic",
        "description": "Assumption and evidence framing a conclusion",
        "bread_relation": "Assumption/evidence",
        "filling_role": "Conclusion",
    },
    {
        "name": "temporal",
        "description": "Before and after states framing a transition",
        "bread_relation": "Before/after",
        "filling_role": "Transition",
    },
    {
        "name": "perspectival",
        "description": "Two viewpoints framing a reconciliation",
        "bread_relation": "Viewpoint A/B",
        "filling_role": "Reconciliation",
    },
    {
        "name": "conditional",
        "description": "Necessary and sufficient conditions framing a target property",
        "bread_relation": "Necessary/sufficient",
        "filling_role": "Target property",
    },
    {
        "name": "stochastic",
        "description": "Prior and likelihood framing a posterior",
        "bread_relation": "Prior/likelihood",
        "filling_role": "Posterior",
    },
    {
        "name": "optimization",
        "description": "Constraints framing an optimum",
        "bread_relation": "Constraints",
        "filling_role": "Optimum",
    },
    {
        "name": "negotiation",
        "description": "Two positions framing a compromise",
        "bread_relation": "Position A/B",
        "filling_role": "Compromise",
    },
    {
        "name": "definitional",
        "description": "Genus and differentia framing a defined concept",
        "bread_relation": "Genus/differentia",
        "filling_role": "Defined concept",
    },
]


def main():
    print(f"Connecting to database: {DATABASE_URL}")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True

    inserted = 0
    skipped = 0

    with conn.cursor() as cur:
        for st in STRUCTURAL_TYPES:
            cur.execute(
                "SELECT 1 FROM structural_types WHERE name = %s", (st["name"],)
            )
            if cur.fetchone():
                print(f"  Skipping '{st['name']}' (already exists)")
                skipped += 1
                continue

            cur.execute(
                """
                INSERT INTO structural_types (name, description, bread_relation, filling_role)
                VALUES (%s, %s, %s, %s)
                """,
                (st["name"], st["description"], st["bread_relation"], st["filling_role"]),
            )
            print(f"  Inserted '{st['name']}'")
            inserted += 1

    print(f"\nDone. Inserted: {inserted}, Skipped: {skipped}")

    # Verify
    with conn.cursor() as cur:
        cur.execute("SELECT type_id, name, description FROM structural_types ORDER BY type_id")
        rows = cur.fetchall()
        print(f"\nStructural types in database ({len(rows)} total):")
        for row in rows:
            print(f"  {row[0]:3d}  {row[1]:20s}  {row[2]}")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
