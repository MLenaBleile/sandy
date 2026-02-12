"""Live Sandwich Feed page.

Real-time stream of sandwich creation with filters and auto-refresh.
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path to import dashboard modules
dashboard_dir = Path(__file__).parent.parent
sys.path.insert(0, str(dashboard_dir))

from components.sandwich_card import sandwich_card
from utils.queries import get_recent_sandwiches, get_structural_types

st.set_page_config(page_title="Live Feed", page_icon="📊", layout="wide")

# Add cute styling to match main page
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #fff5e6 0%, #ffe6f0 100%);
    }
    h1 {
        color: #ff6b9d;
        text-shadow: 2px 2px 4px rgba(255, 182, 193, 0.3);
    }
    h2, h3 {
        color: #ff8fab;
    }
</style>
""", unsafe_allow_html=True)

st.title("🥪 Live Sandwich Feed")

st.markdown("""
<p style='font-size: 1.1rem; color: #666; font-style: italic;'>
    Watch Sandy make sandwiches in real-time! Auto-refreshes every 2 seconds. ✨
</p>
""", unsafe_allow_html=True)

# Filters
col1, col2, col3 = st.columns(3)

with col1:
    validity_min = st.slider(
        "Min Validity",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
        help="Filter sandwiches by minimum validity score"
    )

with col2:
    try:
        all_types = get_structural_types()
        selected_types = st.multiselect(
            "Structural Types",
            options=all_types,
            default=[],
            help="Filter by structural type (empty = all types)"
        )
    except Exception as e:
        st.error(f"Unable to load structural types: {e}")
        selected_types = []
        all_types = []

with col3:
    limit = st.number_input(
        "Limit",
        min_value=5,
        max_value=100,
        value=20,
        step=5,
        help="Maximum number of sandwiches to display"
    )

st.markdown("---")


# Auto-refresh live feed
@st.fragment(run_every="2s")
def live_feed():
    """Auto-refreshing sandwich feed."""

    try:
        sandwiches = get_recent_sandwiches(limit=int(limit))

        if not sandwiches:
            st.info("No sandwiches yet. Run the agent to create some sandwiches!")
            st.code("python -m sandwich.main --max-sandwiches 5", language="bash")
            return

        # Apply filters
        filtered_sandwiches = []
        for sandwich in sandwiches:
            # Validity filter
            if sandwich.get('validity_score', 0.0) < validity_min:
                continue

            # Type filter
            if selected_types and sandwich.get('structural_type') not in selected_types:
                continue

            filtered_sandwiches.append(sandwich)

        # Display count
        st.caption(f"Showing {len(filtered_sandwiches)} of {len(sandwiches)} sandwiches")

        # Render cards
        if not filtered_sandwiches:
            st.warning("No sandwiches match your filters. Try adjusting the criteria.")
        else:
            for sandwich in filtered_sandwiches:
                sandwich_card(sandwich)

    except Exception as e:
        st.error(f"Error loading sandwiches: {e}")
        st.info("Make sure the database is initialized and contains sandwich data.")


# Render the live feed
live_feed()

# Sandy's latest thought (if available)
try:
    recent = get_recent_sandwiches(limit=1)
    if recent and recent[0].get('sandy_commentary'):
        st.markdown("---")
        with st.container():
            st.markdown("### 💭 Sandy's Latest Thought")
            st.markdown("""
            <div style='background: linear-gradient(135deg, #fffbf0 0%, #fff5f8 100%);
                        padding: 1rem;
                        border-radius: 12px;
                        border-left: 4px solid #ff6b9d;
                        font-style: italic;
                        color: #666;'>
                "{}"
            </div>
            """.format(recent[0]['sandy_commentary']), unsafe_allow_html=True)
except Exception:
    pass  # Silently skip if no commentary available

# Cute footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #999; padding: 1rem;'>
    <p style='font-size: 0.9rem; font-style: italic;'>
        🌺 "The internet is vast. Somewhere in it: bread." — Sandy
    </p>
</div>
""", unsafe_allow_html=True)
