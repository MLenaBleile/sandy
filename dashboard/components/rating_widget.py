"""Interactive rating widget for human evaluation of sandwiches."""

import streamlit as st
from typing import Dict, Any

from dashboard.utils.ratings import (
    get_or_create_session_id,
    check_rate_limit,
    has_rated_sandwich,
    save_rating,
    get_human_consensus
)


def rating_widget(
    sandwich: Dict[str, Any],
    show_comparison: bool = True,
    expanded: bool = False
) -> None:
    """Render interactive rating widget for a sandwich.

    Allows users to rate sandwiches on 4 component dimensions + overall.
    Shows real-time comparison between user rating and Sandy's self-assessment.

    Args:
        sandwich: Dictionary containing sandwich data
        show_comparison: If True, show Sandy vs Human comparison after rating
        expanded: If True, expand rating form by default
    """
    sandwich_id = sandwich.get('sandwich_id')

    if not sandwich_id:
        st.warning("Cannot rate sandwich: missing ID")
        return

    session_id = get_or_create_session_id()

    # Check if already rated
    already_rated = has_rated_sandwich(session_id, sandwich_id)

    if already_rated:
        st.info("✅ You've already rated this sandwich! Thanks for your feedback.")

        if show_comparison:
            show_rating_comparison(sandwich)

        return

    # Check rate limit
    is_within_limit, ratings_used = check_rate_limit(session_id, max_ratings=10, window_hours=1)

    if not is_within_limit:
        st.warning(f"⏳ You've reached the rating limit ({ratings_used}/10 per hour). Please try again later.")
        return

    # Show remaining ratings
    remaining = 10 - ratings_used
    st.caption(f"💡 You can submit {remaining} more ratings this hour")

    # Rating form
    with st.expander("🎯 Rate This Sandwich", expanded=expanded):
        st.markdown("""
        Help validate Sandy's self-assessment! Rate each dimension honestly.
        Your ratings are anonymous and help improve the system.
        """)

        with st.form(key=f"rating_form_{sandwich_id}"):
            # Bread Compatibility
            st.markdown("### 🍞 Bread Compatibility")
            st.caption("Are both breads the same type of thing? Do they relate independently of the filling?")
            bread_compat = st.slider(
                "Bread Compatibility Score",
                0.0, 1.0, 0.5, 0.05,
                help="1.0 = Perfect bread pairing, 0.0 = Unrelated breads",
                key=f"bread_{sandwich_id}",
                label_visibility="collapsed"
            )

            # Containment
            st.markdown("### 📦 Containment")
            st.caption("Does the filling genuinely emerge from the space between the breads?")
            containment = st.slider(
                "Containment Score",
                0.0, 1.0, 0.5, 0.05,
                help="1.0 = Filling perfectly bounded, 0.0 = No containment",
                key=f"contain_{sandwich_id}",
                label_visibility="collapsed"
            )

            # Non-triviality / Specificity
            st.markdown("### ✨ Specificity")
            st.caption("Are ingredients concrete and specific, not vague abstractions?")
            nontrivial = st.slider(
                "Specificity Score",
                0.0, 1.0, 0.5, 0.05,
                help="1.0 = Highly specific, 0.0 = Vague/abstract",
                key=f"nontrivial_{sandwich_id}",
                label_visibility="collapsed"
            )

            # Novelty
            st.markdown("### 🌟 Novelty")
            st.caption("How original is this sandwich compared to others you've seen?")
            novelty = st.slider(
                "Novelty Score",
                0.0, 1.0, 0.5, 0.05,
                help="1.0 = Completely novel, 0.0 = Derivative",
                key=f"novelty_{sandwich_id}",
                label_visibility="collapsed"
            )

            # Overall validity
            st.markdown("### ⭐ Overall Validity")
            st.caption("Considering everything, is this a valid sandwich?")
            overall = st.slider(
                "Overall Validity Score",
                0.0, 1.0, 0.5, 0.05,
                help="1.0 = Excellent sandwich, 0.0 = Not a sandwich",
                key=f"overall_{sandwich_id}",
                label_visibility="collapsed"
            )

            # Submit button
            col1, col2 = st.columns([1, 3])
            with col1:
                submitted = st.form_submit_button(
                    "Submit Rating",
                    type="primary",
                    use_container_width=True
                )
            with col2:
                if submitted:
                    st.caption("Submitting...")

            if submitted:
                scores = {
                    'bread_compat': bread_compat,
                    'containment': containment,
                    'nontrivial': nontrivial,
                    'novelty': novelty,
                    'overall': overall
                }

                success = save_rating(sandwich_id, session_id, scores)

                if success:
                    st.success("🎉 Rating saved! Thank you for helping validate Sandy's work.")
                    st.rerun()
                else:
                    st.error("Failed to save rating. Please try again.")


def show_rating_comparison(sandwich: Dict[str, Any]) -> None:
    """Display comparison between Sandy's scores and human consensus.

    Args:
        sandwich: Dictionary containing sandwich data with Sandy's scores
    """
    sandwich_id = sandwich.get('sandwich_id')

    if not sandwich_id:
        return

    human_stats = get_human_consensus(sandwich_id)

    if not human_stats or human_stats['rating_count'] == 0:
        st.info("Be the first to rate this sandwich!")
        return

    st.markdown("### 🤖 vs 👥 Comparison")

    rating_count = human_stats['rating_count']

    # Overall comparison
    col1, col2, col3 = st.columns(3)

    with col1:
        reuben_overall = sandwich.get('validity_score', 0)
        st.metric("🤖 Sandy's Score", f"{reuben_overall:.2f}")

    with col2:
        human_overall = human_stats.get('avg_overall', 0) or 0
        st.metric(
            f"👥 Human Consensus",
            f"{human_overall:.2f}",
            help=f"Based on {rating_count} rating(s)"
        )

    with col3:
        delta = human_overall - reuben_overall
        agreement_color = "normal" if abs(delta) < 0.2 else "inverse"
        st.metric(
            "Agreement",
            f"{delta:+.2f}",
            delta_color=agreement_color
        )

    st.caption(f"📊 Based on {rating_count} human rating(s)")

    # Component breakdown
    st.markdown("**Component Comparison:**")

    components = [
        ('🍞 Bread Compat', 'bread_compat_score', 'avg_bread_compat'),
        ('📦 Containment', 'containment_score', 'avg_containment'),
        ('✨ Specificity', 'nontrivial_score', 'avg_nontrivial'),
        ('🌟 Novelty', 'novelty_score', 'avg_novelty')
    ]

    for label, reuben_key, human_key in components:
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.write(f"**{label}:**")

        with col2:
            reuben_val = sandwich.get(reuben_key, 0) or 0
            st.write(f"🤖 {reuben_val:.2f}")

        with col3:
            human_val = human_stats.get(human_key, 0) or 0
            delta = human_val - reuben_val
            color = "🟢" if abs(delta) < 0.15 else "🟡" if abs(delta) < 0.3 else "🔴"
            st.write(f"👥 {human_val:.2f} {color}")
