"""Analytics Dashboard page.

Component score correlation and validity distribution.
"""

import streamlit as st
import plotly.express as px
import sys
from pathlib import Path
from scipy.stats import f_oneway

# Add parent directory to path
project_root = Path(__file__).parent.parent
dashboard_dir = project_root / "dashboard"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(dashboard_dir))

from utils.queries import get_all_component_scores

st.set_page_config(page_title="Analytics", page_icon="📈", layout="wide")

st.title("📈 Analytics Dashboard")

st.markdown("---")

# Correlation Matrix
st.subheader("Component Score Correlation Matrix")

try:
    all_scores_df = get_all_component_scores()

    if not all_scores_df.empty and len(all_scores_df) >= 3:
        # Select numeric columns for correlation
        score_cols = ['bread_compat_score', 'containment_score', 'nontrivial_score', 'novelty_score', 'validity_score']
        corr_matrix = all_scores_df[score_cols].corr()

        # Create heatmap
        fig = px.imshow(
            corr_matrix,
            labels=dict(color="Correlation"),
            x=['Bread Compat', 'Containment', 'Non-trivial', 'Novelty', 'Validity'],
            y=['Bread Compat', 'Containment', 'Non-trivial', 'Novelty', 'Validity'],
            color_continuous_scale='RdBu_r',
            zmin=-1,
            zmax=1,
            text_auto='.2f'
        )

        fig.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=0, b=0)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        st.caption("Correlation values range from -1 (negative correlation) to +1 (positive correlation). Values near 0 indicate no linear relationship.")

        # Find strongest correlations (excluding diagonal)
        corr_values = []
        for i in range(len(corr_matrix)):
            for j in range(i+1, len(corr_matrix)):
                corr_values.append({
                    'pair': f"{score_cols[i]} ↔ {score_cols[j]}",
                    'correlation': corr_matrix.iloc[i, j]
                })

        if corr_values:
            strongest = max(corr_values, key=lambda x: abs(x['correlation']))
            st.info(f"**Strongest correlation:** {strongest['pair']} (r = {strongest['correlation']:.3f})")
    else:
        st.info("Need at least 3 sandwiches with component scores for correlation analysis.")

except Exception as e:
    st.error(f"Error computing correlation matrix: {e}")

st.markdown("---")

# Box Plots by Structural Type with ANOVA
st.subheader("Validity Distribution by Structural Type")

try:
    all_scores_df = get_all_component_scores()

    if not all_scores_df.empty:
        # Get unique types
        types = all_scores_df['structural_type'].unique()

        if len(types) >= 2:
            # Create box plot
            fig = px.box(
                all_scores_df,
                x='structural_type',
                y='validity_score',
                color='structural_type',
                labels={'structural_type': 'Structural Type', 'validity_score': 'Validity Score'},
                color_discrete_sequence=px.colors.qualitative.Pastel
            )

            fig.update_layout(
                height=400,
                margin=dict(l=0, r=0, t=20, b=0),
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)

            # Perform ANOVA test if we have enough data
            if len(types) >= 2 and all(len(all_scores_df[all_scores_df['structural_type'] == t]) >= 2 for t in types):
                try:
                    # Group data by type
                    groups = [all_scores_df[all_scores_df['structural_type'] == t]['validity_score'].values for t in types]

                    # ANOVA test
                    f_stat, p_value = f_oneway(*groups)

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("ANOVA F-statistic", f"{f_stat:.3f}")
                    with col2:
                        st.metric("P-value", f"{p_value:.4f}")

                    if p_value < 0.05:
                        st.success("Statistically significant difference between structural types (p < 0.05)")
                    else:
                        st.info("No significant difference between structural types (p >= 0.05)")

                except Exception as anova_error:
                    st.warning(f"ANOVA test failed: {anova_error}")
            else:
                st.caption("Need at least 2 samples per type for ANOVA test.")
        else:
            st.info("Need at least 2 different structural types for comparison.")
    else:
        st.info("No component score data available yet.")

except Exception as e:
    st.error(f"Error creating box plots: {e}")
