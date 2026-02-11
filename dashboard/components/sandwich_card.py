"""Sandwich card component for displaying sandwiches in the dashboard.

Uses pure Streamlit native components - NO HTML to avoid rendering issues.
"""

import streamlit as st
from .colors import COLORS, get_structural_type_color, get_validity_color
from typing import Dict, Any


def sandwich_card(sandwich: Dict[str, Any], expanded: bool = False, enable_rating: bool = False) -> None:
    """Render a sandwich card using only Streamlit native components with cute styling.

    Args:
        sandwich: Dictionary containing sandwich data
        expanded: If True, show full details by default
        enable_rating: If True, show rating widget
    """
    validity_score = sandwich.get('validity_score', 0.0)
    structural_type = sandwich.get('structural_type', 'unknown')

    validity_color = get_validity_color(validity_score)
    type_color = get_structural_type_color(structural_type)

    # Cute card styling with inline CSS
    st.markdown(f"""
    <style>
        .sandwich-card {{
            background: linear-gradient(135deg, #fffbf0 0%, #fff5f8 100%);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
            border-left: 4px solid {type_color};
            box-shadow: 0 2px 8px rgba(255, 107, 157, 0.1);
        }}
    </style>
    """, unsafe_allow_html=True)

    # Create a container with border using st.container
    with st.container():
        # Header row
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"### 🥪 {sandwich.get('name', 'Unnamed Sandwich')}")
        with col2:
            # Show validity score as a metric with cute styling
            st.metric("⭐", f"{validity_score:.2f}", delta=None)

        # Sandwich layers - using cute emojis and styled text
        st.markdown(f"**🍞 Top Bread:** {sandwich.get('bread_top', 'Top bread')}")
        st.markdown(f"**🥓 Filling:** {sandwich.get('filling', 'Filling')}")
        st.markdown(f"**🍞 Bottom Bread:** {sandwich.get('bread_bottom', 'Bottom bread')}")

        # Metadata with cute icons
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"🏷️ Type: {structural_type}")
        with col2:
            if 'created_at' in sandwich:
                created_str = str(sandwich['created_at'])[:19]
                st.caption(f"📅 Created: {created_str}")

        # Expandable details
        if sandwich.get('description') or sandwich.get('sandy_commentary'):
            with st.expander("💭 View Details", expanded=expanded):
                if sandwich.get('description'):
                    st.write("**📖 Description:**")
                    st.write(sandwich['description'])

                if sandwich.get('sandy_commentary'):
                    st.write("**🌺 Sandy's Commentary:**")
                    st.info(sandwich['sandy_commentary'])

                # Component scores with cute styling
                if sandwich.get('bread_compat_score') is not None:
                    st.write("**📊 Component Scores:**")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("🍞 Bread", f"{sandwich.get('bread_compat_score', 0.0):.2f}")
                    with col2:
                        st.metric("📦 Contain", f"{sandwich.get('containment_score', 0.0):.2f}")
                    with col3:
                        st.metric("✨ NonTriv", f"{sandwich.get('nontrivial_score', 0.0):.2f}")
                    with col4:
                        st.metric("🌟 Novel", f"{sandwich.get('novelty_score', 0.0):.2f}")

        # Add rating widget if enabled
        if enable_rating:
            st.markdown("---")
            # Import here to avoid circular dependency
            from dashboard.components.rating_widget import rating_widget
            rating_widget(sandwich, show_comparison=True, expanded=False)

        st.markdown("---")


def validity_badge(validity_score: float) -> str:
    """Return validity score as string (for display purposes)."""
    return f"{validity_score:.2f}"
