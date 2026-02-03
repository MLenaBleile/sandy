#!/usr/bin/env python3
"""Browse Reuben's sandwiches from the database.

Usage:
    python scripts/browse.py              # List all sandwiches
    python scripts/browse.py --detail     # Show full details
    python scripts/browse.py --best       # Show top 5 by validity
    python scripts/browse.py --stats      # Show corpus statistics
"""

import argparse
import os
import sys

import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get(
    "SANDWICH_DATABASE__URL",
    "postgresql://sandwich:sandwich@localhost:5433/sandwich",
)


def get_conn():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    return conn


def list_sandwiches(conn, limit=50):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT s.sandwich_id, s.name, s.bread_top, s.filling, s.bread_bottom,
                   s.validity_score, s.bread_compat_score, s.containment_score,
                   s.nontrivial_score, s.novelty_score,
                   st.name as structure_type,
                   s.created_at
            FROM sandwiches s
            LEFT JOIN structural_types st ON s.structural_type_id = st.type_id
            ORDER BY s.created_at DESC
            LIMIT %s
        """, (limit,))
        return cur.fetchall()


def get_sandwich_detail(conn, sandwich_id):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT s.*, st.name as structure_type, src.url as source_url, src.domain
            FROM sandwiches s
            LEFT JOIN structural_types st ON s.structural_type_id = st.type_id
            LEFT JOIN sources src ON s.source_id = src.source_id
            WHERE s.sandwich_id = %s
        """, (sandwich_id,))
        return cur.fetchone()


def get_ingredients(conn, sandwich_id):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT i.text, i.ingredient_type, si.role, i.usage_count
            FROM sandwich_ingredients si
            JOIN ingredients i ON si.ingredient_id = i.ingredient_id
            WHERE si.sandwich_id = %s
            ORDER BY si.role
        """, (sandwich_id,))
        return cur.fetchall()


def get_stats(conn):
    stats = {}
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM sandwiches")
        stats["total_sandwiches"] = cur.fetchone()[0]

        cur.execute("SELECT AVG(validity_score), MIN(validity_score), MAX(validity_score) FROM sandwiches")
        row = cur.fetchone()
        stats["avg_validity"] = row[0]
        stats["min_validity"] = row[1]
        stats["max_validity"] = row[2]

        cur.execute("SELECT COUNT(*) FROM ingredients")
        stats["total_ingredients"] = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM sources")
        stats["total_sources"] = cur.fetchone()[0]

        cur.execute("""
            SELECT st.name, COUNT(*) as cnt
            FROM sandwiches s
            JOIN structural_types st ON s.structural_type_id = st.type_id
            GROUP BY st.name
            ORDER BY cnt DESC
        """)
        stats["type_counts"] = cur.fetchall()

        cur.execute("""
            SELECT text, ingredient_type, usage_count
            FROM ingredients
            ORDER BY usage_count DESC
            LIMIT 10
        """)
        stats["top_ingredients"] = cur.fetchall()

    return stats


def print_sandwich_row(s, index=None):
    prefix = f"  {index}." if index else " "
    validity = f"{s['validity_score']:.2f}" if s['validity_score'] else "n/a"
    print(f"{prefix} {s['name']}")
    print(f"      [{s['structure_type'] or '?'}] validity={validity}")
    print(f"      {s['bread_top']}  |  {s['filling']}  |  {s['bread_bottom']}")
    print()


def print_sandwich_detail(s, ingredients):
    print(f"\n{'=' * 60}")
    print(f"  {s['name']}")
    print(f"{'=' * 60}")
    print(f"  ID:           {s['sandwich_id']}")
    print(f"  Created:      {s['created_at']}")
    print(f"  Structure:    {s['structure_type'] or 'unknown'}")
    print(f"  Source:       {s.get('source_url') or 'n/a'} ({s.get('domain') or '?'})")
    print()
    print(f"  Bread Top:    {s['bread_top']}")
    print(f"  Filling:      {s['filling']}")
    print(f"  Bread Bottom: {s['bread_bottom']}")
    print()

    v = s['validity_score']
    print(f"  Validity:     {v:.2f}" if v else "  Validity:     n/a")
    if s['bread_compat_score'] is not None:
        print(f"    Bread Compat:  {s['bread_compat_score']:.2f}")
        print(f"    Containment:   {s['containment_score']:.2f}")
        spec = s.get('specificity_score')
        if spec is not None:
            print(f"    Specificity:   {spec:.2f}")
        print(f"    Nontrivial:    {s['nontrivial_score']:.2f}")
        print(f"    Novelty:       {s['novelty_score']:.2f}")

    if s.get('description'):
        print(f"\n  Description:")
        print(f"    {s['description']}")

    if s.get('assembly_rationale'):
        print(f"\n  Containment Argument:")
        print(f"    {s['assembly_rationale']}")

    if s.get('validation_rationale'):
        print(f"\n  Validator's Rationale:")
        print(f"    {s['validation_rationale']}")

    if s.get('reuben_commentary'):
        print(f"\n  Reuben's Commentary:")
        print(f"    {s['reuben_commentary']}")

    if ingredients:
        print(f"\n  Ingredients:")
        for ing in ingredients:
            print(f"    [{ing['role']}] {ing['text']} (used {ing['usage_count']}x)")

    print(f"\n{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(description="Browse Reuben's sandwiches")
    parser.add_argument("--detail", action="store_true", help="Show full details for all sandwiches")
    parser.add_argument("--best", action="store_true", help="Show top 5 by validity score")
    parser.add_argument("--stats", action="store_true", help="Show corpus statistics")
    parser.add_argument("--id", type=str, default=None, help="Show detail for a specific sandwich ID")
    parser.add_argument("--limit", type=int, default=50, help="Max sandwiches to list")
    args = parser.parse_args()

    try:
        conn = get_conn()
    except Exception as e:
        print(f"Could not connect to database: {e}")
        print(f"Is the database running? Try: docker compose up db -d")
        return 1

    if args.stats:
        stats = get_stats(conn)
        print(f"\n{'=' * 60}")
        print(f"  CORPUS STATISTICS")
        print(f"{'=' * 60}")
        print(f"  Total sandwiches:  {stats['total_sandwiches']}")
        print(f"  Total ingredients: {stats['total_ingredients']}")
        print(f"  Total sources:     {stats['total_sources']}")
        if stats['avg_validity']:
            print(f"  Validity: avg={stats['avg_validity']:.2f}  "
                  f"min={stats['min_validity']:.2f}  max={stats['max_validity']:.2f}")
        if stats['type_counts']:
            print(f"\n  Structure types:")
            for name, cnt in stats['type_counts']:
                print(f"    {name}: {cnt}")
        if stats['top_ingredients']:
            print(f"\n  Most-used ingredients:")
            for text, itype, count in stats['top_ingredients']:
                print(f"    [{itype}] {text} ({count}x)")
        print(f"\n{'=' * 60}")
        conn.close()
        return 0

    if args.id:
        s = get_sandwich_detail(conn, args.id)
        if not s:
            print(f"Sandwich {args.id} not found.")
            conn.close()
            return 1
        ingredients = get_ingredients(conn, args.id)
        print_sandwich_detail(s, ingredients)
        conn.close()
        return 0

    sandwiches = list_sandwiches(conn, limit=args.limit)
    if not sandwiches:
        print("No sandwiches in the database yet. Run Reuben first!")
        conn.close()
        return 0

    if args.best:
        sandwiches = sorted(sandwiches, key=lambda s: s['validity_score'] or 0, reverse=True)[:5]
        print(f"\n  TOP 5 SANDWICHES BY VALIDITY\n")
    else:
        print(f"\n  ALL SANDWICHES ({len(sandwiches)} total)\n")

    if args.detail:
        for s in sandwiches:
            full = get_sandwich_detail(conn, s['sandwich_id'])
            ingredients = get_ingredients(conn, s['sandwich_id'])
            print_sandwich_detail(full, ingredients)
    else:
        for i, s in enumerate(sandwiches, 1):
            print_sandwich_row(s, i)

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
