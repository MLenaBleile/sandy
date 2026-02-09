"""Streamlit Cloud entry point for Reuben Dashboard.

This file serves as the main entry point when deploying to Streamlit Cloud.
"""

import sys
from pathlib import Path

# Add dashboard directory to Python path
dashboard_dir = Path(__file__).parent / "dashboard"
sys.path.insert(0, str(dashboard_dir))

# Streamlit will automatically execute this script
# Just import the app module and it will run
exec(open(dashboard_dir / "app.py").read())
