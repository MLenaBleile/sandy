"""Analytics Dashboard page.

Research-grade metrics and trends visualization.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path
import pandas as pd

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
    get_component_scores
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

    # 2. Validity Score Distribution
    st.subheader("Validity Score Distribution")

    try:
        validity_df = get_validity_distribution()

        if not validity_df.empty:
            fig = px.histogram(
                validity_df,
                x='validity_score',
                nbins=20,
                title='',
                labels={'validity_score': 'Validity Score'},
                color_discrete_sequence=[COLORS['accent']]
            )

            fig.update_layout(
                height=300,
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)

            # Summary stats
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Mean", f"{validity_df['validity_score'].mean():.2f}")
            with col_b:
                st.metric("Median", f"{validity_df['validity_score'].median():.2f}")
            with col_c:
                st.metric("Std Dev", f"{validity_df['validity_score'].std():.2f}")
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
                    height=300,
                    margin=dict(l=0, r=0, t=0, b=0)
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No component score data available yet.")
        else:
            st.info("No component score data available yet.")

    except Exception as e:
        st.error(f"Error loading component scores: {e}")

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
