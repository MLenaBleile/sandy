# 🚀 Reuben Dashboard - Quick Deployment Checklist

Follow these steps in order to deploy your dashboard!

## ✅ Step 1: Cloud Database Setup (5 minutes)

- [ ] Go to https://neon.tech and sign up (free, no credit card)
- [ ] Create new project: "reuben-sandwich"
- [ ] Copy connection string (looks like: `postgresql://user:pass@ep-xxx.neon.tech/reuben?sslmode=require`)
- [ ] Save connection string somewhere safe

## ✅ Step 2: Initialize Cloud Database (2 minutes)

```bash
# Export your Neon connection string
export DATABASE_URL="your-neon-connection-string-here"

# Initialize schema
psql "$DATABASE_URL" < src/sandwich/db/init_schema.sql
```

**OR** if you don't have psql installed locally:
```bash
# Use Docker psql
docker run --rm -i postgres:15 psql "$DATABASE_URL" < src/sandwich/db/init_schema.sql
```

## ✅ Step 3: Push to GitHub (3 minutes)

- [ ] Initialize git (if not done): `git init`
- [ ] Create GitHub repository at https://github.com/new
  - Name: `reuben-dashboard` (or your choice)
  - Visibility: **Public** (required for free Streamlit Cloud)
- [ ] Add remote: `git remote add origin https://github.com/YOUR_USERNAME/reuben-dashboard.git`
- [ ] Commit and push:
  ```bash
  git add .
  git commit -m "Reuben dashboard with cute theming 🥪"
  git push -u origin main
  ```

## ✅ Step 4: Deploy to Streamlit Cloud (3 minutes)

- [ ] Go to https://share.streamlit.io/
- [ ] Click "New app"
- [ ] Connect your GitHub account (if needed)
- [ ] Select repository: `YOUR_USERNAME/reuben-dashboard`
- [ ] Main file path: `streamlit_app.py`
- [ ] Click "Advanced settings"
- [ ] In "Secrets" section, paste:
  ```toml
  DATABASE_URL = "your-neon-connection-string-here"
  ```
- [ ] Click "Deploy"
- [ ] Wait 2-3 minutes ☕

## ✅ Step 5: Test Your Deployment (1 minute)

- [ ] Dashboard URL will be: `https://YOUR_USERNAME-reuben-dashboard.streamlit.app`
- [ ] Check that the page loads with cute Reuben theming
- [ ] Verify existing sandwiches appear (if you migrated data)
- [ ] Check all pages work (Live Feed, Browser, Analytics, etc.)

## ✅ Step 6: Run Agent with Cloud Database (optional)

To add more sandwiches that will show up on your public dashboard:

```bash
# Set cloud database URL locally
export DATABASE_URL="your-neon-connection-string-here"

# Run agent (when Prompts 4-10 are implemented)
python -m sandwich.main --max-sandwiches 5

# Watch sandwiches appear on your dashboard in real-time!
```

## 🎉 You're Live!

Your dashboard is now publicly accessible at:
```
https://YOUR_USERNAME-reuben-dashboard.streamlit.app
```

Share this URL with anyone! They can:
- ✨ View all Reuben's sandwiches
- 📊 See live updates when you run the agent
- 🗺️ Explore the network graph
- 📈 View analytics and metrics

## 📝 Quick Reference

**Neon Dashboard**: https://console.neon.tech/
**Streamlit Cloud Dashboard**: https://share.streamlit.io/
**GitHub Repository**: https://github.com/YOUR_USERNAME/reuben-dashboard

## 🔄 Making Updates

When you want to update the dashboard:

```bash
# Make your changes
# Then commit and push
git add .
git commit -m "Describe your changes"
git push

# Streamlit Cloud auto-redeploys in 1-2 minutes!
```

## ❓ Need Help?

See the full deployment guide: `DEPLOYMENT.md`

---

*"I could make sandwiches... and now everyone can see them!"* — Reuben 🥪✨
