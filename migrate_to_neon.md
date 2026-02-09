# Migrating Data to Neon Database

You've added the DATABASE_URL to Streamlit secrets - great! Now you need to:
1. Initialize the database schema in Neon
2. Migrate your existing 23 sandwiches from local database to Neon

## Step 1: Get Your Neon Connection String

From the Streamlit secrets you just added, copy your DATABASE_URL. It should look like:
```
postgresql://username:password@ep-something-12345.us-east-2.aws.neon.tech/neondb?sslmode=require
```

## Step 2: Initialize Schema in Neon

Run this command to create all the tables in your Neon database:

```bash
# Replace YOUR_NEON_URL with your actual connection string
psql "postgresql://username:password@ep-something-12345.us-east-2.aws.neon.tech/neondb?sslmode=require" < src/sandwich/db/init_schema.sql
```

**Don't have psql installed?** Use Docker instead:
```bash
docker run --rm -i -v "C:\Users\merli\OneDrive\Documents\reuben:/work" postgres:15 psql "YOUR_NEON_URL" < /work/src/sandwich/db/init_schema.sql
```

## Step 3: Export Data from Local Database

Export your 23 sandwiches from the local Docker database:

```bash
docker exec reuben-db-1 pg_dump -U sandwich -d sandwich --data-only -t sandwiches -t sources -t structural_types > local_sandwiches.sql
```

## Step 4: Import Data to Neon

Import the exported data to Neon:

```bash
psql "YOUR_NEON_URL" < local_sandwiches.sql
```

**Or with Docker:**
```bash
docker run --rm -i -v "C:\Users\merli\OneDrive\Documents\reuben:/work" postgres:15 psql "YOUR_NEON_URL" < /work/local_sandwiches.sql
```

## Step 5: Verify Migration

Check that your data made it:

```bash
psql "YOUR_NEON_URL" -c "SELECT COUNT(*) FROM sandwiches;"
```

You should see: `23`

## Done! 🎉

Your Streamlit dashboard should now show your sandwiches! Refresh https://reuben.streamlit.app and you should see:
- 🥪 Total Sandwiches: 23
- All your sandwiches in the Live Feed page
- Analytics charts populated with data

---

## Future Sandwich Creation

When you want to add more sandwiches that appear on the public dashboard:

1. Run the agent locally with the Neon database URL:
```bash
export DATABASE_URL="your-neon-url-here"
python -m sandwich.main --max-sandwiches 5
```

2. New sandwiches will automatically appear on your public dashboard within 2 seconds!
