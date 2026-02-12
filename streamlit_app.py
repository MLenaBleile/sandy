"""Streamlit Cloud entry point for Sandy Dashboard.

This file serves as the main entry point when deploying to Streamlit Cloud.
It sets up paths, then delegates to dashboard/app.py's main() function.

Streamlit Cloud uses the root pages/ directory for multi-page navigation.
"""

import sys
from pathlib import Path

# Add dashboard directory to Python path so imports work
project_root = Path(__file__).parent
dashboard_dir = project_root / "dashboard"

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(dashboard_dir))

# Import streamlit first
import streamlit as st
import os

# Debug: Check if DATABASE_URL is available
if hasattr(st, 'secrets') and 'DATABASE_URL' in st.secrets:
    print("✓ DATABASE_URL found in Streamlit secrets", file=sys.stderr)
elif os.getenv('DATABASE_URL'):
    print("✓ DATABASE_URL found in environment", file=sys.stderr)
else:
    print("❌ DATABASE_URL not found in secrets or environment!", file=sys.stderr)

# Import and run the dashboard main page
from dashboard.app import main

main()
