import os
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    print("Please set it with:")
    print('export DATABASE_URL="your-neon-connection-string"')
    exit(1)

print(f"Testing connection to Neon...")
print(f"URL (masked): {DATABASE_URL[:30]}...{DATABASE_URL[-20:]}")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT version()")
    version = cur.fetchone()[0]
    print(f"\nOK Connected successfully!")
    print(f"PostgreSQL version: {version[:50]}...")

    # Check existing tables
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = [row[0] for row in cur.fetchall()]
    print(f"\nExisting tables: {tables}")

    # Check sandwiches table structure if it exists
    if 'sandwiches' in tables:
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'sandwiches'
            AND column_name LIKE '%commentary%'
        """)
        cols = cur.fetchall()
        print(f"\nCommentary columns in sandwiches table: {cols}")

    cur.close()
    conn.close()

except Exception as e:
    print(f"\nX Connection failed: {e}")
    exit(1)
