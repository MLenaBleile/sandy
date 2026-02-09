"""Sandwich Browser page.

Searchable, filterable interface to the entire sandwich corpus.
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.parent
dashboard_dir = project_root / "dashboard"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(dashboard_dir))

from dashboard.components.sandwich_card import sandwich_card
from dashboard.utils.queries import search_sandwiches, get_structural_types, get_source_domains

st.set_page_config(page_title="Browser", page_icon="🔍", layout="wide")

st.title("🔍 Sandwich Browser")

st.markdown("Search and explore the entire sandwich corpus with advanced filters.")

# Sidebar filters
with st.sidebar:
    st.header("Filters")

    # Validity range
    validity_range = st.slider(
        "Validity Range",
        min_value=0.0,
        max_value=1.0,
        value=(0.5, 1.0),
        step=0.05,
        help="Filter by validity score range"
    )

    # Structural type filter
    try:
        all_types = get_structural_types()
        selected_types = st.multiselect(
            "Structural Types",
            options=all_types,
            default=[],
            help="Leave empty to show all types"
        )
    except Exception as e:
        st.error(f"Error loading types: {e}")
        selected_types = []

    # Source domain filter
    try:
        all_domains = get_source_domains()
        selected_domains = st.multiselect(
            "Source Domains",
            options=all_domains,
            default=[],
            help="Leave empty to show all sources"
        )
    except Exception as e:
        st.error(f"Error loading domains: {e}")
        selected_domains = []

    # Results per page
    page_size = st.number_input(
        "Results per page",
        min_value=10,
        max_value=100,
        value=20,
        step=10
    )

# Search bar
search_query = st.text_input(
    "🔎 Search",
    placeholder="Search sandwich names, descriptions, bread, or filling...",
    help="Case-insensitive search across all text fields"
)

# Pagination state
if 'page' not in st.session_state:
    st.session_state.page = 0

st.markdown("---")

# Search and display
try:
    offset = st.session_state.page * page_size

    df = search_sandwiches(
        query=search_query,
        validity_min=validity_range[0],
        validity_max=validity_range[1],
        types=selected_types if selected_types else None,
        limit=page_size,
        offset=offset
    )

    if df.empty:
        st.info("No sandwiches found matching your criteria. Try adjusting the filters or search query.")
    else:
        # Display as table
        st.dataframe(
            df[['name', 'validity_score', 'structural_type', 'source_domain', 'created_at']],
            use_container_width=True,
            hide_index=True
        )

        # Pagination controls
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if st.button("⬅️ Previous", disabled=(st.session_state.page == 0)):
                st.session_state.page -= 1
                st.rerun()

        with col2:
            st.write(f"Page {st.session_state.page + 1}")

        with col3:
            # Disable next if we got fewer results than page_size
            if st.button("Next ➡️", disabled=(len(df) < page_size)):
                st.session_state.page += 1
                st.rerun()

        st.markdown("---")

        # Detail view for selected sandwich
        st.subheader("Sandwich Details")

        # Convert DataFrame back to dict for sandwich_card
        sandwiches_list = df.to_dict('records')

        # Display all sandwiches in current page
        for sandwich in sandwiches_list:
            sandwich_card(sandwich, expanded=False)

except Exception as e:
    st.error(f"Error searching sandwiches: {e}")
    st.info("Make sure the database is initialized and accessible.")
