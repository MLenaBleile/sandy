"""Human Ratings Analytics - Sandy vs Human Consensus Analysis"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path

# Add project root and dashboard to path
project_root = Path(__file__).parent.parent
dashboard_dir = project_root / "dashboard"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(dashboard_dir))

from dashboard.utils.queries import (
    get_rating_stats,
    get_reuben_vs_human_comparison,
    get_most_controversial_sandwiches,
    get_component_comparison
)

st.set_page_config(page_title="Human Ratings", page_icon="👥", layout="wide")

# Add cute styling
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

st.title("👥 Human Ratings Analysis")
st.markdown("Compare Sandy's self-assessment with human consensus")

# Overall statistics
stats = get_rating_stats()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Ratings", stats.get('total_ratings', 0))

with col2:
    st.metric("Sandwiches Rated", stats.get('unique_sandwiches', 0))

with col3:
    st.metric("Unique Raters", stats.get('unique_raters', 0))

with col4:
    # Calculate average agreement
    comparison_data = get_reuben_vs_human_comparison()
    if comparison_data:
        df = pd.DataFrame(comparison_data)
        avg_diff = abs(df['Sandy_score'] - df['human_score']).mean()
        agreement_pct = 100 - (avg_diff * 100)
        st.metric("Agreement", f"{agreement_pct:.1f}%")
    else:
        st.metric("Agreement", "N/A")

st.markdown("---")

# Check if we have enough data
if not comparison_data or len(comparison_data) < 3:
    st.info("""
    ### 📊 Not Enough Data Yet

    We need at least 3 ratings per sandwich to show meaningful analysis.

    **Get started:**
    1. Visit the **Live Feed** or **Browser** pages
    2. Rate some sandwiches using the rating widget
    3. Come back here to see the analysis!

    Each sandwich needs at least 3 human ratings before appearing in comparisons.
    """)
    st.stop()

# Scatter plot: Sandy vs Human
st.subheader("🤖 Sandy vs 👥 Human Consensus")

df = pd.DataFrame(comparison_data)

fig = px.scatter(
    df, x='Sandy_score', y='human_score',
    color='structural_type', size='rating_count',
    hover_data=['name'],
    title="Sandy's Score vs Human Consensus",
    labels={'Sandy_score': "Sandy's Score", 'human_score': 'Human Consensus'},
    color_discrete_sequence=px.colors.qualitative.Pastel
)

# Add diagonal line (perfect agreement)
fig.add_trace(go.Scatter(
    x=[0, 1], y=[0, 1],
    mode='lines', name='Perfect Agreement',
    line=dict(color='gray', dash='dash', width=2)
))

fig.update_layout(height=500, xaxis_range=[0, 1], yaxis_range=[0, 1])
st.plotly_chart(fig, use_container_width=True)

# Correlation analysis
if len(df) >= 3:
    correlation = df['Sandy_score'].corr(df['human_score'])

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Pearson Correlation", f"{correlation:.3f}")

    with col2:
        if correlation > 0.7:
            st.success("✅ Strong agreement between Sandy and humans!")
        elif correlation > 0.4:
            st.info("📊 Moderate agreement - some systematic differences exist.")
        else:
            st.warning("⚠️ Low agreement - Sandy's self-assessment may need calibration.")

st.markdown("---")

# Biggest disagreements
st.subheader("🎯 Biggest Disagreements")

controversial = get_most_controversial_sandwiches(limit=10)

if controversial:
    st.markdown("These sandwiches show the largest gap between Sandy's self-assessment and human ratings:")

    for sandwich in controversial[:5]:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            st.write(f"**{sandwich['name']}**")
            st.caption(f"Type: {sandwich['structural_type']}")

        with col2:
            st.write(f"🤖 {sandwich['Sandy_score']:.2f}")

        with col3:
            st.write(f"👥 {sandwich['human_avg']:.2f}")

        with col4:
            delta = sandwich['human_avg'] - sandwich['Sandy_score']
            color = "🔴" if abs(delta) > 0.3 else "🟡"
            st.write(f"{color} {delta:+.2f}")
            st.caption(f"({sandwich['rating_count']} ratings)")
else:
    st.info("Need more ratings to identify controversial sandwiches.")

st.markdown("---")

# Component-level analysis
st.subheader("📊 Component Score Analysis")

component_data = get_component_comparison()

if component_data and component_data.get('Sandy_bread') is not None:
    components = ['Bread Compat', 'Containment', 'Non-trivial', 'Novelty']
    reuben_scores = [
        component_data.get('Sandy_bread', 0) or 0,
        component_data.get('Sandy_contain', 0) or 0,
        component_data.get('Sandy_nontrivial', 0) or 0,
        component_data.get('Sandy_novelty', 0) or 0
    ]
    human_scores = [
        component_data.get('human_bread', 0) or 0,
        component_data.get('human_contain', 0) or 0,
        component_data.get('human_nontrivial', 0) or 0,
        component_data.get('human_novelty', 0) or 0
    ]

    fig = go.Figure(data=[
        go.Bar(name='🤖 Reuben', x=components, y=reuben_scores, marker_color='#ff6b9d'),
        go.Bar(name='👥 Human', x=components, y=human_scores, marker_color='#4a90e2')
    ])

    fig.update_layout(
        barmode='group',
        height=400,
        yaxis_range=[0, 1],
        yaxis_title="Average Score",
        xaxis_title="Component"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Which component has biggest disagreement?
    differences = [abs(r - h) for r, h in zip(reuben_scores, human_scores)]
    if differences:
        max_diff_idx = differences.index(max(differences))
        max_diff = differences[max_diff_idx]

        if max_diff > 0.15:
            st.warning(f"**Biggest disagreement:** {components[max_diff_idx]} (Δ {max_diff:.2f})")
            st.caption("Sandy and humans have different perspectives on this dimension.")
        else:
            st.success(f"✅ Good agreement across all components (max Δ {max_diff:.2f})")
else:
    st.info("Need more ratings for component-level analysis.")

st.markdown("---")

# Insights and recommendations
with st.expander("💡 Insights & Interpretation"):
    st.markdown("""
    ### How to Read This Data

    **Scatter Plot:**
    - Points near the diagonal line = good agreement
    - Points above line = humans rate higher than Reuben
    - Points below line = Sandy rates higher than humans

    **Correlation Coefficient:**
    - > 0.7 = Strong agreement
    - 0.4 - 0.7 = Moderate agreement
    - < 0.4 = Weak agreement (calibration needed)

    **Component Analysis:**
    - Shows which dimensions have most/least agreement
    - Large gaps suggest systematic bias in self-assessment
    - Can inform weight adjustments in validation scoring

    ### Research Applications

    This data enables:
    - **Calibration**: Adjust Sandy's scoring weights based on human feedback
    - **Bias Detection**: Identify which dimensions Sandy over/under-scores
    - **Validation**: Test if sandwich criteria align with human intuition
    - **Quality Control**: Flag sandwiches with high human-AI disagreement for review
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #999; padding: 1rem;'>
    <p style='font-size: 0.9rem; font-style: italic;'>
        🌺 "The human consensus is a treasure. But also, they really like the sandwiches with puns in the name." — Reuben
    </p>
</div>
""", unsafe_allow_html=True)
