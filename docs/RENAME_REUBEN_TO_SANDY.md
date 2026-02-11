# Renaming Reuben to Sandy - Progress Tracker

## Why This Change?
To avoid potential copyright issues with Disney's character "Reuben" from Lilo & Stitch (Experiment 625), we're renaming the agent to "Sandy the Sandwich Agent" - a more distinctive and memorable name that avoids trademark conflicts.

## ✅ Completed

### Documentation
- [x] SPEC.md - All references to Reuben replaced with Sandy
- [x] PROMPTS.md - All references updated
- [x] prompts/personality_preamble.txt - Updated
- [x] prompts/curiosity.txt - Updated
- [x] prompts/identifier.txt - Updated
- [x] prompts/assembler.txt - Updated (including field name change: reuben_commentary → sandy_commentary)

## 🔄 Remaining Work

### Core Source Code
- [ ] src/sandwich/agent/reuben.py → Rename to sandy.py
  - Class name: `class Reuben` → `class Sandy`
  - All internal references

- [ ] src/sandwich/agent/assembler.py
  - Field name: reuben_commentary → sandy_commentary
  - All string references

- [ ] src/sandwich/agent/identifier.py
  - Voice references in error messages

- [ ] src/sandwich/db/models.py
  - Field: reuben_commentary → sandy_commentary in dataclasses

- [ ] src/sandwich/db/repository.py
  - Column references to sandy_commentary

- [ ] src/sandwich/main.py
  - Import: `from sandwich.agent.reuben import Reuben` → `from sandwich.agent.sandy import Sandy`
  - Instantiation: `reuben = Reuben(...)` → `sandy = Sandy(...)`
  - All variable names

- [ ] src/sandwich/llm/anthropic.py
  - Logging references

- [ ] src/sandwich/llm/interface.py
  - Documentation strings

- [ ] src/sandwich/sources/wikipedia.py
  - Comments/docstrings

### Database Schema
- [ ] src/sandwich/db/init_schema.sql
  - Column: reuben_commentary → sandy_commentary in sandwiches table
  - Update migration script

### Tests
- [ ] tests/test_reuben.py → Rename to test_sandy.py
  - Class references
  - Variable names

- [ ] tests/test_assembler.py
  - Field name assertions

- [ ] tests/test_pipeline.py
  - Variable names

- [ ] tests/test_validator.py
  - Commentary field references

### Dashboard
- [ ] dashboard/app.py
  - Title: "Reuben Dashboard" → "Sandy Dashboard"
  - Sidebar references
  - Welcome message

- [ ] dashboard/pages/1_📊_Live_Feed.py
  - "Reuben's latest thought" → "Sandy's latest thought"
  - Commentary references

- [ ] dashboard/pages/5_✨_Interactive.py
  - "Make me a sandwich with Reuben" → "Make me a sandwich with Sandy"
  - Spinner text

- [ ] dashboard/pages/6_⚙️_Settings.py
  - UI labels

- [ ] dashboard/components/sandwich_card.py
  - Field access: sandy_commentary
  - Display labels

- [ ] dashboard/components/rating_widget.py
  - References

- [ ] dashboard/utils/queries.py
  - SQL queries with commentary field

- [ ] dashboard/README.md
  - Project name references

- [ ] dashboard/static/styles.css
  - CSS class names (if any)

### Configuration & Deployment
- [ ] docker-compose.yml
  - Service names (if referencing "reuben")
  - Comments

- [ ] README.md
  - All project description references
  - Example commands

- [ ] DEPLOYMENT.md
  - Instructions mentioning Reuben

- [ ] DEPLOYMENT_CHECKLIST.md
  - References

### Scripts
- [ ] scripts/browse.py
  - Variable names

- [ ] migrate_data.sh / migrate_data.bat
  - Comments

### Data Files (Optional - Can Preserve Historical Data)
- [ ] sandwiches_export.tsv - Commentary column (historical data - can leave as-is)
- [ ] sandwiches_fixed.tsv - Commentary column (historical data - can leave as-is)
- [ ] local_sandwiches.sql - Commentary column (historical data - can leave as-is)
- [ ] local_sandwiches_fixed.sql - Commentary column (historical data - can leave as-is)

## 📝 Systematic Replacement Guide

### Safe Find-and-Replace Operations (Case Sensitive):
1. `reuben_commentary` → `sandy_commentary` (database field)
2. `class Reuben` → `class Sandy` (class definition)
3. `from sandwich.agent.reuben import Reuben` → `from sandwich.agent.sandy import Sandy`
4. `reuben = Reuben` → `sandy = Sandy`
5. `You are Reuben,` → `You are Sandy,`
6. `Reuben's` → `Sandy's`
7. `Reuben ` → `Sandy ` (with trailing space)

### Files Requiring Manual Review:
- Voice/personality messages (ensure tone remains consistent)
- Comments and docstrings (context-dependent)
- Historical data exports (decide whether to update or preserve)

## 🧪 Testing After Rename

After completing the rename, verify:
1. [ ] All tests pass: `pytest tests/`
2. [ ] Database schema updated correctly
3. [ ] Dashboard loads without errors
4. [ ] Agent can create sandwiches
5. [ ] All imports resolve correctly
6. [ ] No broken references in logs

## 🎯 Priority Order

1. **Core Agent Files** - Get the agent working first
2. **Database Schema** - Ensure data persistence works
3. **Tests** - Verify everything still functions
4. **Dashboard** - Update UI references
5. **Documentation** - Clean up remaining docs

## Notes
- The personality should remain exactly the same - just the name changes
- Sandy should still be "a being of vast intelligence who chooses to make sandwiches"
- Keep the same quiet, contemplative, dry humor
- Database migration may be needed for existing sandwiches with reuben_commentary
