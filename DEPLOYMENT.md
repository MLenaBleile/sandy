# Reuben Dashboard Deployment Guide

This guide will help you deploy the Reuben dashboard to Streamlit Cloud so you can share it with others!

## 🎯 Overview

The deployment architecture:
- **Dashboard**: Hosted on Streamlit Cloud (free)
- **Database**: Cloud PostgreSQL (Neon.tech recommended - free tier available)
- **Agent**: Runs locally on your machine, writes to cloud database

## 📋 Prerequisites

1. GitHub account
2. Streamlit Cloud account (sign up at https://streamlit.io/cloud)
3. Your code pushed to a GitHub repository

## Step 1: Set Up Cloud Database (Neon.tech - Free)

### Create Neon Account
1. Go to https://neon.tech
2. Sign up for free (no credit card required)
3. Create a new project called "reuben-sandwich"

### Get Database Connection String
After creating your project, you'll see a connection string like:
```
postgresql://username:password@ep-something-12345.us-east-2.aws.neon.tech/reuben?sslmode=require
```

**Save this connection string** - you'll need it for both Streamlit Cloud and local agent runs.

### Initialize Database Schema
From your local machine, initialize the cloud database:

```bash
# Set the cloud database URL
export DATABASE_URL="your-neon-connection-string-here"

# Initialize schema
docker exec -i reuben-db-1 psql "$DATABASE_URL" < src/sandwich/db/init_schema.sql

# Or if you have psql installed locally:
psql "$DATABASE_URL" < src/sandwich/db/init_schema.sql
```

### Migrate Existing Data (Optional)
If you want to copy your 23 existing sandwiches to the cloud:

```bash
# Export from local database
docker exec reuben-db-1 pg_dump -U sandwich -d sandwich -t sandwiches -t sources -t structural_types --data-only > local_data.sql

# Import to cloud database
psql "$DATABASE_URL" < local_data.sql
```

## Step 2: Push Code to GitHub

### Initialize Git Repository (if not already done)
```bash
cd C:\Users\merli\OneDrive\Documents\reuben

# Initialize git
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit - Reuben dashboard with cute theming"
```

### Create GitHub Repository
1. Go to https://github.com/new
2. Create a new repository called "reuben-dashboard" (or any name you like)
3. Make it **Public** (required for Streamlit Cloud free tier)
4. Don't initialize with README (we already have code)

### Push to GitHub
```bash
# Add GitHub remote (replace with your username)
git remote add origin https://github.com/YOUR_USERNAME/reuben-dashboard.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 3: Deploy to Streamlit Cloud

### Create Streamlit Cloud App
1. Go to https://share.streamlit.io/
2. Click "New app"
3. Select your GitHub repository: `YOUR_USERNAME/reuben-dashboard`
4. Set **Main file path**: `streamlit_app.py`
5. Click "Advanced settings"

### Configure Secrets
In the Advanced settings, add this to the "Secrets" section:

```toml
DATABASE_URL = "postgresql://username:password@ep-something-12345.us-east-2.aws.neon.tech/reuben?sslmode=require"
```

Replace with your actual Neon connection string.

### Deploy!
1. Click "Deploy"
2. Wait 2-3 minutes for deployment
3. Your dashboard will be live at: `https://YOUR_USERNAME-reuben-dashboard.streamlit.app`

## Step 4: Run Agent Locally with Cloud Database

Now that your dashboard is deployed, you can run the Reuben agent locally and it will write to the cloud database, which the dashboard will display!

### Update Local Configuration
```bash
# Set environment variable to use cloud database
export DATABASE_URL="your-neon-connection-string-here"

# Run the agent (when Prompts 4-10 are implemented)
python -m sandwich.main --max-sandwiches 10
```

### Agent Workflow
1. Run agent locally → creates sandwiches → writes to cloud DB
2. Cloud dashboard automatically shows new sandwiches (refreshes every 2 seconds on Live Feed page)
3. Share dashboard URL with anyone!

## 🎨 Your Deployed Dashboard Features

Your public dashboard will have:
- **Live Feed**: Auto-refreshing sandwich stream
- **Browser**: Search and filter all sandwiches
- **Analytics**: Charts and metrics
- **Exploration**: Network graph visualization
- **Settings**: Export data, configure weights

## 💰 Cost Breakdown (Free Tier)

- **Streamlit Cloud**: Free for public apps
- **Neon.tech Database**: Free tier includes:
  - 512 MB storage
  - 1 project
  - Auto-suspend after 5 minutes of inactivity
  - Perfect for Reuben's needs!
- **Total Monthly Cost**: $0 🎉

## 🔄 Updating Your Deployed App

When you make changes to the code:

```bash
# Make changes to your code
# Then commit and push
git add .
git commit -m "Update: describe your changes"
git push

# Streamlit Cloud will automatically redeploy within 1-2 minutes!
```

## 🔐 Security Notes

### What's Public
- Dashboard UI is publicly accessible
- Anyone can view sandwiches
- Database connection string is kept secret

### What's Private
- Database credentials (in Streamlit secrets)
- Source code (if you make repo private after getting Streamlit Pro)
- Agent runs locally on your machine

## 🐛 Troubleshooting

### "Database connection failed"
- Check your DATABASE_URL in Streamlit secrets
- Verify Neon database is active (not suspended)
- Check connection string includes `?sslmode=require`

### "No sandwiches appearing"
- Make sure database schema is initialized
- Verify you've run the agent with cloud DATABASE_URL
- Check Streamlit Cloud logs for errors

### "App won't deploy"
- Verify `streamlit_app.py` exists in repository root
- Check `requirements-streamlit.txt` has all dependencies
- Review deployment logs in Streamlit Cloud

## 📱 Sharing Your Dashboard

Once deployed, you can share your dashboard URL with:
- Researchers who want to see Reuben's sandwiches
- Friends who enjoy the cute Lilo & Stitch theme
- Anyone interested in AI-generated knowledge structures

Example URL: `https://yourusername-reuben-dashboard.streamlit.app`

## 🚀 Optional: Scheduled Agent Runs

Want Reuben to make sandwiches automatically? Set up a scheduled task:

### Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., "Daily at 3 AM")
4. Action: "Start a program"
5. Program: `python`
6. Arguments: `-m sandwich.main --max-sandwiches 5`
7. Start in: `C:\Users\merli\OneDrive\Documents\reuben`

### macOS/Linux Cron Job
```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 3 AM)
0 3 * * * cd /path/to/reuben && /usr/bin/python -m sandwich.main --max-sandwiches 5
```

## 🎉 You're Done!

Your Reuben dashboard is now live and shareable! Every time you run the agent locally, new sandwiches will appear on the public dashboard within 2 seconds.

---

*"Ohana means family. Family means nobody gets left behind... but if you want a sandwich dashboard, I got you covered."* — Reuben 🥪🌺
