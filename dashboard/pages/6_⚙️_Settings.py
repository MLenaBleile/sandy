"""Settings page.

Configuration, data management, and system controls.
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path
dashboard_dir = Path(__file__).parent.parent
sys.path.insert(0, str(dashboard_dir))

from utils.queries import get_all_sandwiches

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

st.title("⚙️ Settings & Configuration")

st.markdown("Manage dashboard settings, export data, and control agent configuration.")

st.markdown("---")

# Session Control
st.subheader("🎮 Session Control")

st.info("""
**Note:** Session control requires the full agent to be implemented (Prompts 4-10).
These controls will be functional once the agent is complete.
""")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.button("▶️ Start Session", disabled=True, help="Coming soon: Start a new foraging session")

with col2:
    st.button("⏸️ Pause", disabled=True, help="Coming soon: Pause current session")

with col3:
    st.button("▶️ Resume", disabled=True, help="Coming soon: Resume paused session")

with col4:
    st.button("⏹️ Stop", disabled=True, help="Coming soon: Stop current session")

# Current session stats (stubbed)
st.caption("Current session: None")
st.caption("Sandwiches made: 0 | Foraging attempts: 0 | Uptime: 0:00:00")

st.markdown("---")

# Configuration
st.subheader("⚙️ Validation Configuration")

st.markdown("""
Adjust the weights used for sandwich validation. These weights determine how each
component score contributes to the overall validity score.
""")

col1, col2 = st.columns([2, 1])

with col1:
    w_bread = st.slider(
        "Bread Compatibility Weight",
        min_value=0.0,
        max_value=1.0,
        value=0.25,
        step=0.05,
        help="Weight for bread compatibility score"
    )

    w_contain = st.slider(
        "Containment Weight",
        min_value=0.0,
        max_value=1.0,
        value=0.35,
        step=0.05,
        help="Weight for containment score"
    )

    w_nontrivial = st.slider(
        "Non-triviality Weight",
        min_value=0.0,
        max_value=1.0,
        value=0.20,
        step=0.05,
        help="Weight for non-triviality score"
    )

    w_novelty = st.slider(
        "Novelty Weight",
        min_value=0.0,
        max_value=1.0,
        value=0.20,
        step=0.05,
        help="Weight for novelty score"
    )

with col2:
    st.markdown("### Weight Summary")

    total = w_bread + w_contain + w_nontrivial + w_novelty

    st.metric("Total", f"{total:.2f}")

    if abs(total - 1.0) > 0.01:
        st.warning(f"Weights will be normalized to sum to 1.0")

    st.markdown("**Normalized weights:**")
    st.write(f"Bread: {(w_bread/total):.2f}")
    st.write(f"Containment: {(w_contain/total):.2f}")
    st.write(f"Non-trivial: {(w_nontrivial/total):.2f}")
    st.write(f"Novelty: {(w_novelty/total):.2f}")

if st.button("💾 Save Configuration", type="primary"):
    st.info("Configuration saving will be implemented once agent config system is complete.")
    # TODO: Implement actual config save when agent is ready
    # config = SandwichConfig()
    # config.validation.weight_bread_compat = w_bread / total
    # etc.

if st.button("🔄 Reset to Defaults"):
    st.info("Reset functionality will be available once agent config system is complete.")

st.markdown("---")

# Data Management
st.subheader("📥 Data Management")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Export Corpus**")

    if st.button("📄 Export as CSV"):
        try:
            with st.spinner("Exporting corpus..."):
                sandwiches = get_all_sandwiches()

                if sandwiches:
                    df = pd.DataFrame(sandwiches)

                    # Select columns for export
                    export_cols = [
                        'sandwich_id', 'name', 'validity_score',
                        'bread_top', 'filling', 'bread_bottom',
                        'structural_type', 'source_domain', 'source_url',
                        'created_at', 'description', 'sandy_commentary'
                    ]

                    available_cols = [c for c in export_cols if c in df.columns]
                    export_df = df[available_cols]

                    csv = export_df.to_csv(index=False)

                    st.download_button(
                        label="⬇️ Download CSV",
                        data=csv,
                        file_name="Sandy_corpus.csv",
                        mime="text/csv"
                    )

                    st.success(f"Exported {len(sandwiches)} sandwiches")
                else:
                    st.info("No sandwiches to export")

        except Exception as e:
            st.error(f"Export failed: {e}")

    if st.button("📋 Export as JSON"):
        try:
            import json

            with st.spinner("Exporting corpus..."):
                sandwiches = get_all_sandwiches()

                if sandwiches:
                    # Convert UUIDs and datetimes to strings
                    for s in sandwiches:
                        for key, value in s.items():
                            if hasattr(value, 'isoformat'):  # datetime
                                s[key] = value.isoformat()
                            elif hasattr(value, '__str__') and 'UUID' in str(type(value)):
                                s[key] = str(value)

                    json_str = json.dumps(sandwiches, indent=2, default=str)

                    st.download_button(
                        label="⬇️ Download JSON",
                        data=json_str,
                        file_name="Sandy_corpus.json",
                        mime="application/json"
                    )

                    st.success(f"Exported {len(sandwiches)} sandwiches")
                else:
                    st.info("No sandwiches to export")

        except Exception as e:
            st.error(f"Export failed: {e}")

with col2:
    st.markdown("**Cache Management**")

    if st.button("🗑️ Clear Dashboard Cache"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("All caches cleared!")
        st.info("Page will reload with fresh data.")

    st.caption("Clears query caches. Use if data seems stale.")

with col3:
    st.markdown("**Database Management**")

    st.button(
        "🔄 Refresh Materialized Views",
        disabled=True,
        help="Coming soon: Refresh daily_stats and other materialized views"
    )

    st.button(
        "💾 Backup Database",
        disabled=True,
        help="Coming soon: Create database backup"
    )

st.markdown("---")

# Source Management
st.subheader("🌐 Source Management")

st.info("Source management will be available once Prompts 4-10 are complete.")

st.markdown("""
**Planned features:**
- Toggle sources on/off (Wikipedia, ArXiv, News RSS, Web Search)
- Add custom RSS feeds or URLs
- View foraging stats per source (success rate, avg validity)
- Configure rate limits and priorities
""")

st.markdown("---")

# About
with st.expander("ℹ️ About this Dashboard"):
    st.markdown("""
    **Sandy Dashboard v0.1**

    Built with:
    - Streamlit for UI
    - Plotly for visualizations
    - NetworkX for graph analysis
    - PostgreSQL + pgvector for storage

    **Data Flow:**
    1. Sandy agent forages content and creates sandwiches
    2. Sandwiches stored in PostgreSQL database
    3. Dashboard queries database with caching
    4. Real-time updates via event bus (when agent is running)

    **Performance:**
    - Query caching reduces database load
    - Materialized views for expensive aggregations
    - Auto-refresh every 2 seconds on Live Feed
    - Handles 1000+ sandwiches efficiently

    For more information, see SPEC.md Section 14.
    """)

st.caption("Dashboard implementation based on SPEC.md Section 14 and Prompt 13")
