#!/bin/bash
# Migration script for moving sandwich data from local Docker to Neon

set -e  # Exit on error

echo "🥪 Reuben Data Migration Script"
echo "================================"
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable is not set"
    echo ""
    echo "Please set your Neon connection string:"
    echo 'export DATABASE_URL="postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require"'
    exit 1
fi

echo "✓ DATABASE_URL is set"
echo ""

# Step 1: Initialize schema
echo "📋 Step 1: Initializing schema in Neon database..."
psql "$DATABASE_URL" < src/sandwich/db/init_schema.sql
echo "✓ Schema initialized"
echo ""

# Step 2: Export data from local database
echo "📦 Step 2: Exporting data from local Docker database..."
docker exec reuben-db-1 pg_dump -U sandwich -d sandwich \
    --data-only \
    -t sandwiches \
    -t sources \
    -t structural_types \
    > local_sandwiches.sql
echo "✓ Data exported to local_sandwiches.sql"
echo ""

# Step 3: Import data to Neon
echo "☁️  Step 3: Importing data to Neon..."
psql "$DATABASE_URL" < local_sandwiches.sql
echo "✓ Data imported"
echo ""

# Step 4: Verify
echo "🔍 Step 4: Verifying migration..."
SANDWICH_COUNT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM sandwiches;" | tr -d ' ')
echo "✓ Found $SANDWICH_COUNT sandwiches in Neon database"
echo ""

# Step 5: Refresh materialized view
echo "📊 Step 5: Refreshing analytics views..."
psql "$DATABASE_URL" -c "REFRESH MATERIALIZED VIEW daily_stats;" 2>/dev/null || echo "⚠️  Materialized view refresh skipped (may not exist yet)"
echo ""

echo "🎉 Migration complete!"
echo ""
echo "Your dashboard should now show all sandwiches at:"
echo "   https://reuben.streamlit.app"
echo ""
echo "To add more sandwiches, run the agent with:"
echo "   export DATABASE_URL=\"\$DATABASE_URL\""
echo "   python -m sandwich.main --max-sandwiches 5"
