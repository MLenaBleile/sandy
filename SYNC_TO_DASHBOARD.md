# How to Sync Your Local Sandwiches to the Streamlit Dashboard

## Current Situation

- **Local Database**: 45 sandwiches in `localhost:5433`
  - Container: `nostalgic-ride-db-1`
  - 5 new sandwiches just created with Sandy!

- **Streamlit Cloud Dashboard**: Connected to Neon cloud database
  - URL: https://reuben.streamlit.app (will need to update this URL to sandy.streamlit.app or similar)
  - Currently has older data

## ⚠️ Important Notes About Migration Scripts

The migration scripts (`migrate_data.bat` and `migrate_data.sh`) reference `reuben-db-1` but your actual container is `nostalgic-ride-db-1`.

You have two options:

### Option 1: Fix the Script (Recommended)

Update the container name in the migration script before running:

**In migrate_data.sh** (line 30):
```bash
# Change from:
docker exec reuben-db-1 pg_dump -U sandwich -d sandwich ...

# To:
docker exec nostalgic-ride-db-1 pg_dump -U sandwich -d sandwich ...
```

**In migrate_data.bat** (line 36):
```batch
REM Change from:
docker exec reuben-db-1 pg_dump -U sandwich -d sandwich ...

REM To:
docker exec nostalgic-ride-db-1 pg_dump -U sandwich -d sandwich ...
```

### Option 2: Just Export/Import Manually

Since you have the working database, you can manually export and import:

```bash
# 1. Set your Neon DATABASE_URL
export DATABASE_URL="postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require"

# 2. Export from local
docker exec nostalgic-ride-db-1 pg_dump -U sandwich -d sandwich \
    --data-only \
    -t sandwiches \
    -t sources \
    -t structural_types \
    > local_sandwiches.sql

# 3. Import to Neon
psql "$DATABASE_URL" < local_sandwiches.sql

# 4. Verify
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM sandwiches;"
```

## 🔄 What Will Happen When You Push to GitHub

### Code Changes (Automatic)
When you `git push` the renamed files:

✅ **Streamlit Cloud will automatically**:
1. Detect the changes
2. Redeploy the dashboard
3. Use the new code with "Sandy" references
4. Update the UI to show `sandy_commentary` field

❌ **It will NOT automatically**:
1. Sync your local sandwiches to Neon
2. Update the database data

### Data Sync (Manual)
You need to run the migration script manually to sync sandwiches.

## 📋 Step-by-Step: Complete Update Process

### Step 1: Fix Migration Script Container Name

Edit either `migrate_data.sh` or `migrate_data.bat` and change `reuben-db-1` to `nostalgic-ride-db-1`.

### Step 2: Get Your Neon DATABASE_URL

You should have this in your Streamlit secrets. It looks like:
```
postgresql://username:password@ep-something.us-east-2.aws.neon.tech/neondb?sslmode=require
```

### Step 3: Run Database Migration

**On Windows:**
```batch
set DATABASE_URL=postgresql://your-neon-url
migrate_data.bat
```

**On Linux/Mac/Git Bash:**
```bash
export DATABASE_URL="postgresql://your-neon-url"
./migrate_data.sh
```

This will:
- Initialize schema in Neon (if needed)
- Export all 45 sandwiches from local DB
- Import them to Neon
- Verify the count

### Step 4: Push Code to GitHub

```bash
git add .
git commit -m "Rename agent from Reuben to Sandy

- Renamed reuben.py -> sandy.py throughout codebase
- Updated all imports and references
- Changed database column: reuben_commentary -> sandy_commentary
- Updated logging and UI text
- Database migration completed locally
- 45 sandwiches ready for cloud sync"

git push origin main
```

### Step 5: Verify Dashboard

After pushing:
1. Wait 1-2 minutes for Streamlit Cloud to redeploy
2. Visit your dashboard URL
3. Check that:
   - ✅ Sandwiches appear (should see all 45)
   - ✅ UI says "Sandy" not "Reuben"
   - ✅ Commentary field displays correctly

## 🎯 Quick Command Summary

```bash
# 1. Update migration script container name
# (edit migrate_data.sh or migrate_data.bat manually)

# 2. Set Neon URL and migrate
export DATABASE_URL="your-neon-url"
./migrate_data.sh  # or migrate_data.bat on Windows

# 3. Push to GitHub
git add .
git commit -m "Rename Reuben to Sandy - complete"
git push origin main
```

## 🔍 Troubleshooting

**If migration fails:**
- Check that `nostalgic-ride-db-1` is running: `docker ps`
- Verify DATABASE_URL is set: `echo $DATABASE_URL`
- Make sure you can connect to Neon: `psql "$DATABASE_URL" -c "SELECT 1;"`

**If dashboard doesn't update:**
- Check Streamlit Cloud logs for deployment errors
- Verify the database migration ran successfully
- Clear browser cache and refresh

**If column name errors appear:**
- The migration script will handle the schema
- Make sure you pushed the code WITH the updated schema file
