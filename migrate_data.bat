@echo off
REM Migration script for moving sandwich data from local Docker to Neon (Windows version)

echo 🥪 Reuben Data Migration Script
echo ================================
echo.

REM Check if DATABASE_URL is set
if "%DATABASE_URL%"=="" (
    echo ❌ ERROR: DATABASE_URL environment variable is not set
    echo.
    echo Please set your Neon connection string:
    echo set DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require
    echo.
    echo Then run this script again.
    pause
    exit /b 1
)

echo ✓ DATABASE_URL is set
echo.

REM Step 1: Initialize schema
echo 📋 Step 1: Initializing schema in Neon database...
docker run --rm -i -v "%CD%:/work" postgres:15 psql "%DATABASE_URL%" < src/sandwich/db/init_schema.sql
if errorlevel 1 (
    echo ❌ Failed to initialize schema
    pause
    exit /b 1
)
echo ✓ Schema initialized
echo.

REM Step 2: Export data from local database
echo 📦 Step 2: Exporting data from local Docker database...
docker exec reuben-db-1 pg_dump -U sandwich -d sandwich --data-only -t sandwiches -t sources -t structural_types > local_sandwiches.sql
if errorlevel 1 (
    echo ❌ Failed to export data
    pause
    exit /b 1
)
echo ✓ Data exported to local_sandwiches.sql
echo.

REM Step 3: Import data to Neon
echo ☁️  Step 3: Importing data to Neon...
docker run --rm -i -v "%CD%:/work" postgres:15 psql "%DATABASE_URL%" < local_sandwiches.sql
if errorlevel 1 (
    echo ❌ Failed to import data
    pause
    exit /b 1
)
echo ✓ Data imported
echo.

REM Step 4: Verify
echo 🔍 Step 4: Verifying migration...
docker run --rm postgres:15 psql "%DATABASE_URL%" -t -c "SELECT COUNT(*) FROM sandwiches;"
echo.

echo 🎉 Migration complete!
echo.
echo Your dashboard should now show all sandwiches at:
echo    https://reuben.streamlit.app
echo.
echo To add more sandwiches, run the agent with:
echo    set DATABASE_URL=%DATABASE_URL%
echo    python -m sandwich.main --max-sandwiches 5
echo.
pause
