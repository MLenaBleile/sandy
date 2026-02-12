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
from sklearn.ensemble import IsolationForest
from datetime import datetime, timedelta

# Add parent directory to path
project_root = Path(__file__).parent.parent
dashboard_dir = project_root / "dashboard"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(dashboard_dir))

from components.colors import COLORS
from utils.queries import (
    get_foraging_efficiency,
    get_validity_distribution,
    get_structural_type_stats,
    get_component_scores,
    get_all_component_scores,
    get_sandwiches_with_timestamps
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

# Multivariate Anomaly Detection (Isolation Forest)
st.subheader("Multivariate Anomaly Detection")
st.caption("Uses Isolation Forest to detect anomalies across all component scores simultaneously")

try:
    all_scores_df = get_all_component_scores()

    if not all_scores_df.empty and len(all_scores_df) >= 10:
        # Prepare features for Isolation Forest
        feature_cols = ['bread_compat_score', 'containment_score', 'nontrivial_score', 'novelty_score', 'validity_score']
        X = all_scores_df[feature_cols].values

        # Fit Isolation Forest
        iso_forest = IsolationForest(
            contamination=0.1,  # Expect 10% anomalies
            random_state=42,
            n_estimators=100
        )

        predictions = iso_forest.fit_predict(X)
        anomaly_scores = iso_forest.score_samples(X)

        # Add to dataframe
        all_scores_df['is_anomaly'] = predictions == -1
        all_scores_df['anomaly_score'] = anomaly_scores

        # Find anomalies
        multivariate_anomalies = all_scores_df[all_scores_df['is_anomaly']]

        if len(multivariate_anomalies) > 0:
            st.warning(f"⚠️ Found {len(multivariate_anomalies)} multivariate anomalies (unusual combinations of scores)")

            # Display anomalies
            anomaly_display = multivariate_anomalies[['structural_type', 'validity_score', 'anomaly_score']].copy()
            anomaly_display['anomaly_score'] = anomaly_display['anomaly_score'].round(3)
            anomaly_display['validity_score'] = anomaly_display['validity_score'].round(3)
            anomaly_display = anomaly_display.sort_values('anomaly_score')

            st.dataframe(
                anomaly_display.head(10),
                column_config={
                    'structural_type': 'Type',
                    'validity_score': 'Validity',
                    'anomaly_score': 'Anomaly Score'
                },
                hide_index=True,
                use_container_width=True
            )

            st.caption("Lower anomaly scores indicate more unusual combinations. Isolation Forest identifies sandwiches that are 'easy to isolate' from the rest.")

            # Visualize anomalies in 2D (using PCA-like projection)
            fig = px.scatter(
                all_scores_df,
                x='validity_score',
                y='bread_compat_score',
                color='is_anomaly',
                color_discrete_map={True: 'red', False: 'lightblue'},
                labels={'validity_score': 'Validity Score', 'bread_compat_score': 'Bread Compat Score'},
                title='Anomaly Detection: Validity vs Bread Compat'
            )

            fig.update_layout(height=400, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.success("✅ No multivariate anomalies detected")
    else:
        st.info("Need at least 10 sandwiches for multivariate anomaly detection.")

except Exception as e:
    st.error(f"Error in multivariate anomaly detection: {e}")

st.markdown("---")

# Temporal Anomaly Detection
st.subheader("Temporal Anomaly Detection")
st.caption("Detects unusual spikes or drops in sandwich creation rate")

try:
    temporal_df = get_sandwiches_with_timestamps()

    if not temporal_df.empty and len(temporal_df) >= 7:
        # Group by date
        temporal_df['date'] = temporal_df['created_at'].dt.date
        daily_counts = temporal_df.groupby('date').size().reset_index(name='count')

        # Convert to datetime for plotting
        daily_counts['date'] = pd.to_datetime(daily_counts['date'])

        # Calculate Z-scores for creation rate
        mean_count = daily_counts['count'].mean()
        std_count = daily_counts['count'].std()

        if std_count > 0:
            daily_counts['z_score'] = (daily_counts['count'] - mean_count) / std_count

            # Flag anomalies
            daily_counts['is_anomaly'] = abs(daily_counts['z_score']) > 2.0

            # Plot creation rate over time
            fig = go.Figure()

            # Normal days
            normal_days = daily_counts[~daily_counts['is_anomaly']]
            fig.add_trace(go.Scatter(
                x=normal_days['date'],
                y=normal_days['count'],
                mode='lines+markers',
                name='Normal',
                line=dict(color=COLORS['accent'], width=2),
                marker=dict(size=6)
            ))

            # Anomalous days
            if daily_counts['is_anomaly'].any():
                anomalous_days = daily_counts[daily_counts['is_anomaly']]
                fig.add_trace(go.Scatter(
                    x=anomalous_days['date'],
                    y=anomalous_days['count'],
                    mode='markers',
                    name='Anomaly',
                    marker=dict(size=12, color='red', symbol='star')
                ))

            # Add mean line
            fig.add_hline(
                y=mean_count,
                line_dash="dash",
                line_color="gray",
                annotation_text=f"Mean: {mean_count:.1f}",
                annotation_position="right"
            )

            fig.update_layout(
                title='Sandwiches Created Per Day',
                xaxis_title='Date',
                yaxis_title='Count',
                height=400,
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)

            # Display anomalous days
            anomalous_days = daily_counts[daily_counts['is_anomaly']]
            if len(anomalous_days) > 0:
                st.warning(f"⚠️ Found {len(anomalous_days)} days with unusual creation rates")

                anomaly_display = anomalous_days[['date', 'count', 'z_score']].copy()
                anomaly_display['z_score'] = anomaly_display['z_score'].round(2)
                anomaly_display['date'] = anomaly_display['date'].dt.strftime('%Y-%m-%d')

                st.dataframe(
                    anomaly_display,
                    column_config={
                        'date': 'Date',
                        'count': 'Sandwiches Created',
                        'z_score': 'Z-Score'
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.success("✅ No temporal anomalies detected in creation rate")
        else:
            st.info("All days have same creation rate - no anomalies possible")
    else:
        st.info("Need at least 7 days of data for temporal anomaly detection")

except Exception as e:
    st.error(f"Error in temporal anomaly detection: {e}")

st.markdown("---")

# Quality Drift Detection
st.subheader("Quality Drift Detection")
st.caption("Monitors rolling average validity score to detect quality degradation over time")

try:
    temporal_df = get_sandwiches_with_timestamps()

    if not temporal_df.empty and len(temporal_df) >= 10:
        # Sort by time
        temporal_df = temporal_df.sort_values('created_at')

        # Calculate rolling average (window=10)
        window_size = min(10, len(temporal_df) // 2)
        temporal_df['rolling_avg'] = temporal_df['validity_score'].rolling(window=window_size, min_periods=1).mean()

        # Calculate overall trend
        if len(temporal_df) >= 3:
            x = np.arange(len(temporal_df))
            slope, intercept = np.polyfit(x, temporal_df['validity_score'], 1)

            # Plot
            fig = go.Figure()

            # Individual scores
            fig.add_trace(go.Scatter(
                x=temporal_df['created_at'],
                y=temporal_df['validity_score'],
                mode='markers',
                name='Individual Scores',
                marker=dict(size=6, color=COLORS['accent'], opacity=0.5)
            ))

            # Rolling average
            fig.add_trace(go.Scatter(
                x=temporal_df['created_at'],
                y=temporal_df['rolling_avg'],
                mode='lines',
                name=f'Rolling Avg ({window_size})',
                line=dict(color='blue', width=3)
            ))

            # Trend line
            trend_y = slope * x + intercept
            fig.add_trace(go.Scatter(
                x=temporal_df['created_at'],
                y=trend_y,
                mode='lines',
                name='Trend',
                line=dict(color='red', width=2, dash='dash')
            ))

            fig.update_layout(
                title='Validity Score Over Time',
                xaxis_title='Creation Date',
                yaxis_title='Validity Score',
                height=400,
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)

            # Interpret trend
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Trend Slope", f"{slope:.4f}")

            with col2:
                if slope < -0.001:
                    st.error("📉 Quality is degrading over time")
                elif slope > 0.001:
                    st.success("📈 Quality is improving over time")
                else:
                    st.info("➡️ Quality is stable")

            st.caption("Trend slope indicates change in validity per sandwich. Negative values suggest quality degradation.")
        else:
            st.info("Need at least 3 sandwiches for trend analysis")
    else:
        st.info("Need at least 10 sandwiches for quality drift detection")

except Exception as e:
    st.error(f"Error in quality drift detection: {e}")

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
