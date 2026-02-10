"""Analytics Dashboard page.

Research-grade metrics and trends visualization.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import shapiro, f_oneway

# Add parent directory to path
project_root = Path(__file__).parent.parent
dashboard_dir = project_root / "dashboard"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(dashboard_dir))

from dashboard.components.colors import COLORS
from dashboard.utils.queries import (
    get_foraging_efficiency,
    get_validity_distribution,
    get_structural_type_stats,
    get_component_scores,
    get_all_component_scores
)

st.set_page_config(page_title="Analytics", page_icon="📈", layout="wide")

st.title("📈 Analytics Dashboard")

st.markdown("Deep dive into corpus statistics, trends, and patterns.")

st.markdown("---")

# Two-column layout
col1, col2 = st.columns(2)

# LEFT COLUMN
with col1:
    # 1. Foraging Efficiency Over Time
    st.subheader("Foraging Efficiency Over Time")

    try:
        efficiency_df = get_foraging_efficiency()

        if not efficiency_df.empty:
            # Calculate success rate
            efficiency_df['success_rate'] = (efficiency_df['successes'] / efficiency_df['attempts']) * 100

            fig = px.line(
                efficiency_df,
                x='date',
                y='success_rate',
                title='',
                labels={'success_rate': 'Success Rate (%)', 'date': 'Date'}
            )

            fig.update_traces(line_color=COLORS['accent'], line_width=3)
            fig.update_layout(
                height=300,
                margin=dict(l=0, r=0, t=0, b=0),
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)

            # Stats
            avg_rate = efficiency_df['success_rate'].mean()
            st.caption(f"Average success rate: {avg_rate:.1f}%")
        else:
            st.info("No foraging data available yet.")

    except Exception as e:
        st.error(f"Error loading foraging efficiency: {e}")

    st.markdown("---")

    # 2. Validity Score Distribution with Statistical Overlays
    st.subheader("Validity Score Distribution")

    try:
        validity_df = get_validity_distribution()

        if not validity_df.empty and len(validity_df) >= 3:
            # Calculate statistics
            mean_val = validity_df['validity_score'].mean()
            median_val = validity_df['validity_score'].median()
            std_val = validity_df['validity_score'].std()

            # Create histogram
            fig = px.histogram(
                validity_df,
                x='validity_score',
                nbins=20,
                title='',
                labels={'validity_score': 'Validity Score'},
                color_discrete_sequence=[COLORS['accent']],
                opacity=0.7
            )

            # Add mean line
            fig.add_vline(
                x=mean_val,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Mean: {mean_val:.2f}",
                annotation_position="top"
            )

            # Add median line
            fig.add_vline(
                x=median_val,
                line_dash="dot",
                line_color="green",
                annotation_text=f"Median: {median_val:.2f}",
                annotation_position="bottom"
            )

            # Add std dev bands
            fig.add_vrect(
                x0=mean_val - std_val,
                x1=mean_val + std_val,
                fillcolor="gray",
                opacity=0.1,
                line_width=0,
                annotation_text="±1σ",
                annotation_position="top left"
            )

            fig.update_layout(
                height=300,
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)

            # Summary stats with normality test
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("Mean", f"{mean_val:.2f}")
            with col_b:
                st.metric("Median", f"{median_val:.2f}")
            with col_c:
                st.metric("Std Dev", f"{std_val:.2f}")
            with col_d:
                # Shapiro-Wilk test for normality (only if n >= 3)
                if len(validity_df) >= 3:
                    try:
                        stat, p_value = shapiro(validity_df['validity_score'])
                        is_normal = "✓" if p_value > 0.05 else "✗"
                        st.metric("Normal", f"{is_normal} (p={p_value:.3f})")
                    except Exception:
                        st.metric("Normal", "N/A")
                else:
                    st.metric("Normal", "N/A")
        else:
            st.info("No validity data available yet.")

    except Exception as e:
        st.error(f"Error loading validity distribution: {e}")

# RIGHT COLUMN
with col2:
    # 3. Structural Type Heatmap
    st.subheader("Structural Type × Source Domain")

    try:
        stats_df = get_structural_type_stats()

        if not stats_df.empty:
            # Pivot for heatmap
            heatmap_data = stats_df.pivot(
                index='structure_type',
                columns='domain',
                values='sandwich_count'
            ).fillna(0)

            fig = px.imshow(
                heatmap_data,
                labels=dict(x="Source Domain", y="Structural Type", color="Count"),
                color_continuous_scale='Blues',
                aspect="auto"
            )

            fig.update_layout(
                height=300,
                margin=dict(l=0, r=0, t=0, b=0)
            )

            st.plotly_chart(fig, use_container_width=True)

            st.caption(f"Total unique combinations: {len(stats_df)}")
        else:
            st.info("No structural type data available yet.")

    except Exception as e:
        st.error(f"Error loading structural type stats: {e}")

    st.markdown("---")

    # 4. Component Score Breakdown (Radar Chart)
    st.subheader("Component Score Breakdown")

    try:
        component_df = get_component_scores()

        if not component_df.empty:
            # Create radar chart for first structural type (or allow selection)
            if len(component_df) > 0:
                # Let user select which type to display
                selected_type = st.selectbox(
                    "Select structural type",
                    options=component_df['structural_type'].tolist(),
                    key="radar_type_selector"
                )

                type_data = component_df[component_df['structural_type'] == selected_type].iloc[0]

                categories = ['Bread Compat', 'Containment', 'Non-trivial', 'Novelty']
                values = [
                    type_data['avg_bread_compat'],
                    type_data['avg_containment'],
                    type_data['avg_nontrivial'],
                    type_data['avg_novelty']
                ]

                fig = go.Figure(data=go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name=selected_type,
                    line_color=COLORS['accent']
                ))

                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 1]
                        )
                    ),
                    showlegend=False,
                    height=400,
                    margin=dict(l=80, r=80, t=40, b=40)
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No component score data available yet.")
        else:
            st.info("No component score data available yet.")

    except Exception as e:
        st.error(f"Error loading component scores: {e}")

st.markdown("---")

# STATISTICAL ANALYSIS SECTION
st.header("📊 Statistical Analysis")

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
                        st.success("✅ Statistically significant difference between structural types (p < 0.05)")
                    else:
                        st.info("📊 No significant difference between structural types (p ≥ 0.05)")

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

st.markdown("---")

# Outlier Detection
st.subheader("Statistical Outliers")

try:
    all_scores_df = get_all_component_scores()

    if not all_scores_df.empty and len(all_scores_df) >= 3:
        # Calculate Z-scores for validity
        mean_validity = all_scores_df['validity_score'].mean()
        std_validity = all_scores_df['validity_score'].std()

        if std_validity > 0:
            all_scores_df['z_score'] = (all_scores_df['validity_score'] - mean_validity) / std_validity

            # Flag outliers (|Z| > 2.5)
            outliers = all_scores_df[abs(all_scores_df['z_score']) > 2.5]

            if len(outliers) > 0:
                st.warning(f"⚠️ Found {len(outliers)} statistical outliers (|Z-score| > 2.5)")

                # Display outliers
                outlier_display = outliers[['structural_type', 'validity_score', 'z_score']].copy()
                outlier_display['z_score'] = outlier_display['z_score'].round(2)
                outlier_display['validity_score'] = outlier_display['validity_score'].round(3)

                st.dataframe(
                    outlier_display,
                    column_config={
                        'structural_type': 'Type',
                        'validity_score': 'Validity',
                        'z_score': 'Z-Score'
                    },
                    hide_index=True,
                    use_container_width=True
                )

                st.caption("Z-score indicates how many standard deviations away from the mean. Values beyond ±2.5 are considered unusual.")
            else:
                st.success("✅ No statistical outliers detected (all |Z-scores| ≤ 2.5)")
        else:
            st.info("Insufficient variance to detect outliers.")
    else:
        st.info("Need at least 3 sandwiches for outlier detection.")

except Exception as e:
    st.error(f"Error detecting outliers: {e}")

st.markdown("---")

# Export functionality
st.subheader("📥 Export Data")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Export Validity Data"):
        try:
            validity_df = get_validity_distribution()
            if not validity_df.empty:
                csv = validity_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="validity_distribution.csv",
                    mime="text/csv"
                )
        except Exception as e:
            st.error(f"Export failed: {e}")

with col2:
    if st.button("Export Efficiency Data"):
        try:
            efficiency_df = get_foraging_efficiency()
            if not efficiency_df.empty:
                csv = efficiency_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="foraging_efficiency.csv",
                    mime="text/csv"
                )
        except Exception as e:
            st.error(f"Export failed: {e}")

with col3:
    if st.button("Export Type Stats"):
        try:
            stats_df = get_structural_type_stats()
            if not stats_df.empty:
                csv = stats_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="structural_type_stats.csv",
                    mime="text/csv"
                )
        except Exception as e:
            st.error(f"Export failed: {e}")
