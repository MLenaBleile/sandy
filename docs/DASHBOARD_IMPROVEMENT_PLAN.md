# 🥪 Reuben Dashboard - Comprehensive Improvement Plan

## Executive Summary

Transform the dashboard from a "pretty reporting tool" into a **research-grade analytics platform** with human-in-the-loop evaluation, statistical rigor, and advanced data science features.

**Timeline:** 3-4 weeks
**Effort:** ~80-100 hours
**Priority:** High-impact features first, then advanced analytics

---

## Phase 1: Critical Foundations (Week 1) - MUST DO

### 1.1 Database Schema & Performance (Priority: CRITICAL)

**Issue:** Missing indexes, inefficient queries, no human rating capability

**Tasks:**
- [ ] Add database indexes for performance
- [ ] Create `human_ratings` table for visitor feedback
- [ ] Add full-text search indexes (pg_trgm)
- [ ] Create materialized views for expensive aggregations
- [ ] Implement connection pooling

**Files to modify:**
- `src/sandwich/db/init_schema.sql`
- `dashboard/utils/db.py`

**SQL Migration:**
```sql
-- Performance indexes
CREATE INDEX idx_sandwiches_created_at ON sandwiches(created_at DESC);
CREATE INDEX idx_sandwiches_validity ON sandwiches(validity_score);
CREATE INDEX idx_sandwiches_type ON sandwiches(structural_type_id);
CREATE INDEX idx_sandwiches_validity_type_created
    ON sandwiches(validity_score, structural_type_id, created_at DESC);

-- Full-text search
CREATE INDEX idx_sandwiches_name_trgm ON sandwiches USING gin(name gin_trgm_ops);
CREATE INDEX idx_sandwiches_description_trgm ON sandwiches USING gin(description gin_trgm_ops);

-- Human ratings table
CREATE TABLE human_ratings (
    rating_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sandwich_id UUID REFERENCES sandwiches(sandwich_id) ON DELETE CASCADE,
    session_id UUID NOT NULL,
    bread_compat_score FLOAT NOT NULL,
    containment_score FLOAT NOT NULL,
    nontrivial_score FLOAT NOT NULL,
    novelty_score FLOAT NOT NULL,
    overall_validity FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    user_agent TEXT,
    ip_hash TEXT,  -- Hashed for privacy
    CONSTRAINT valid_scores CHECK (
        bread_compat_score BETWEEN 0 AND 1 AND
        containment_score BETWEEN 0 AND 1 AND
        nontrivial_score BETWEEN 0 AND 1 AND
        novelty_score BETWEEN 0 AND 1 AND
        overall_validity BETWEEN 0 AND 1
    )
);

CREATE INDEX idx_ratings_sandwich ON human_ratings(sandwich_id);
CREATE INDEX idx_ratings_session ON human_ratings(session_id);
CREATE INDEX idx_ratings_created ON human_ratings(created_at DESC);

-- Materialized view for type stats
CREATE MATERIALIZED VIEW mv_structural_type_stats AS
SELECT
    st.name as structural_type,
    src.domain,
    COUNT(*) as sandwich_count,
    AVG(s.validity_score) as avg_validity,
    AVG(s.bread_compat_score) as avg_bread_compat,
    AVG(s.containment_score) as avg_containment,
    AVG(s.nontrivial_score) as avg_nontrivial,
    AVG(s.novelty_score) as avg_novelty
FROM sandwiches s
JOIN structural_types st ON s.structural_type_id = st.type_id
LEFT JOIN sources src ON s.source_id = src.source_id
GROUP BY st.name, src.domain;

CREATE INDEX idx_mv_type_stats ON mv_structural_type_stats(structural_type, domain);

-- Refresh trigger (call periodically)
CREATE OR REPLACE FUNCTION refresh_mv_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_structural_type_stats;
END;
$$ LANGUAGE plpgsql;
```

**Database utilities update:**
```python
# dashboard/utils/db.py
from psycopg2.pool import ThreadedConnectionPool

_pool = None

@st.cache_resource
def get_db_pool():
    """Get or create connection pool."""
    global _pool
    if _pool is None:
        database_url = os.getenv('DATABASE_URL') or st.secrets.get('DATABASE_URL')
        _pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=5,
            dsn=database_url
        )
    return _pool

def get_db_connection():
    """Get connection from pool."""
    pool = get_db_pool()
    return pool.getconn()

def return_db_connection(conn):
    """Return connection to pool."""
    pool = get_db_pool()
    pool.putconn(conn)
```

**Impact:** 10-100x query speedup, enables human rating feature
**Time:** 6-8 hours

---

### 1.2 Human Rating System (Priority: HIGH)

**Issue:** No way to validate Reuben's self-assessment against human judgment

**Tasks:**
- [ ] Create rating widget component
- [ ] Implement session tracking (anonymous)
- [ ] Add rating submission logic
- [ ] Show real-time Reuben vs Human comparison
- [ ] Add rate limiting (10 ratings per session per hour)
- [ ] Create human ratings analytics queries

**New files:**
- `dashboard/components/rating_widget.py`
- `dashboard/utils/ratings.py`

**Rating Widget Component:**
```python
# dashboard/components/rating_widget.py
import streamlit as st
import uuid
from datetime import datetime, timedelta
from dashboard.utils.db import execute_query

def get_or_create_session_id():
    """Get or create anonymous session ID."""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    return st.session_state.session_id

def check_rate_limit(session_id: str, max_ratings: int = 10, window_hours: int = 1) -> bool:
    """Check if session has exceeded rate limit."""
    query = """
        SELECT COUNT(*) as rating_count
        FROM human_ratings
        WHERE session_id = %s
        AND created_at > NOW() - INTERVAL '%s hours'
    """
    result = execute_query(query, (session_id, window_hours), fetch_one=True)
    return result['rating_count'] < max_ratings if result else True

def has_rated_sandwich(session_id: str, sandwich_id: str) -> bool:
    """Check if session already rated this sandwich."""
    query = """
        SELECT COUNT(*) as count
        FROM human_ratings
        WHERE session_id = %s AND sandwich_id = %s
    """
    result = execute_query(query, (session_id, sandwich_id), fetch_one=True)
    return result['count'] > 0 if result else False

def save_rating(sandwich_id: str, session_id: str, scores: dict):
    """Save human rating to database."""
    query = """
        INSERT INTO human_ratings (
            sandwich_id, session_id,
            bread_compat_score, containment_score,
            nontrivial_score, novelty_score, overall_validity
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    execute_query(query, (
        sandwich_id, session_id,
        scores['bread_compat'], scores['containment'],
        scores['nontrivial'], scores['novelty'], scores['overall']
    ))

def get_human_consensus(sandwich_id: str) -> dict:
    """Get aggregated human ratings for a sandwich."""
    query = """
        SELECT
            COUNT(*) as rating_count,
            AVG(bread_compat_score) as avg_bread_compat,
            AVG(containment_score) as avg_containment,
            AVG(nontrivial_score) as avg_nontrivial,
            AVG(novelty_score) as avg_novelty,
            AVG(overall_validity) as avg_overall,
            STDDEV(overall_validity) as std_overall
        FROM human_ratings
        WHERE sandwich_id = %s
    """
    return execute_query(query, (sandwich_id,), fetch_one=True)

def rating_widget(sandwich: dict, show_comparison: bool = True):
    """Interactive rating widget for a sandwich."""
    sandwich_id = sandwich['sandwich_id']
    session_id = get_or_create_session_id()

    # Check if already rated
    already_rated = has_rated_sandwich(session_id, sandwich_id)

    if already_rated:
        st.info("✅ You've already rated this sandwich! Thanks for your feedback.")
        if show_comparison:
            show_rating_comparison(sandwich)
        return

    # Check rate limit
    if not check_rate_limit(session_id):
        st.warning("⏳ You've reached the rating limit. Please try again later.")
        return

    st.markdown("### 🎯 Rate This Sandwich")
    st.caption("Help us validate Reuben's self-assessment!")

    with st.form(key=f"rating_form_{sandwich_id}"):
        st.markdown("**How well do the breads relate to each other?**")
        bread_compat = st.slider(
            "🍞 Bread Compatibility",
            0.0, 1.0, 0.5, 0.05,
            help="Are both breads the same type of thing? Do they relate independently of the filling?"
        )

        st.markdown("**How well is the filling bounded by the breads?**")
        containment = st.slider(
            "📦 Containment",
            0.0, 1.0, 0.5, 0.05,
            help="Does the filling genuinely emerge from the space between the breads?"
        )

        st.markdown("**How specific are the ingredients?**")
        nontrivial = st.slider(
            "✨ Non-trivial",
            0.0, 1.0, 0.5, 0.05,
            help="Are ingredients concrete and specific, not vague abstractions?"
        )

        st.markdown("**How original is this sandwich?**")
        novelty = st.slider(
            "🌟 Novelty",
            0.0, 1.0, 0.5, 0.05,
            help="Is this distinct from other sandwiches you've seen?"
        )

        st.markdown("**Overall, is this a valid sandwich?**")
        overall = st.slider(
            "⭐ Overall Validity",
            0.0, 1.0, 0.5, 0.05,
            help="Your overall assessment of sandwich quality"
        )

        submitted = st.form_submit_button("Submit Rating", type="primary")

        if submitted:
            scores = {
                'bread_compat': bread_compat,
                'containment': containment,
                'nontrivial': nontrivial,
                'novelty': novelty,
                'overall': overall
            }
            save_rating(sandwich_id, session_id, scores)
            st.success("🎉 Rating saved! Thank you for helping validate Reuben's work.")
            st.rerun()

def show_rating_comparison(sandwich: dict):
    """Show comparison between Reuben's scores and human consensus."""
    sandwich_id = sandwich['sandwich_id']
    human_stats = get_human_consensus(sandwich_id)

    if not human_stats or human_stats['rating_count'] == 0:
        st.info("No human ratings yet. Be the first to rate!")
        return

    st.markdown("### 🤖 vs 👥 Comparison")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("🤖 Reuben's Overall", f"{sandwich['validity_score']:.2f}")

    with col2:
        st.metric(
            f"👥 Human Consensus (n={human_stats['rating_count']})",
            f"{human_stats['avg_overall']:.2f}"
        )

    with col3:
        delta = human_stats['avg_overall'] - sandwich['validity_score']
        st.metric("Δ Agreement", f"{delta:+.2f}")

    # Component breakdown comparison
    st.markdown("**Component Score Comparison:**")

    components = [
        ('Bread Compat', 'bread_compat_score', 'avg_bread_compat'),
        ('Containment', 'containment_score', 'avg_containment'),
        ('Non-trivial', 'nontrivial_score', 'avg_nontrivial'),
        ('Novelty', 'novelty_score', 'avg_novelty')
    ]

    for label, reuben_key, human_key in components:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"**{label}:**")
        with col2:
            st.write(f"🤖 {sandwich.get(reuben_key, 0):.2f}")
        with col3:
            human_val = human_stats.get(human_key, 0) or 0
            delta = human_val - sandwich.get(reuben_key, 0)
            st.write(f"👥 {human_val:.2f} ({delta:+.2f})")
```

**Integration into sandwich_card.py:**
```python
# dashboard/components/sandwich_card.py
from dashboard.components.rating_widget import rating_widget

def sandwich_card(sandwich: Dict[str, Any], expanded: bool = False, enable_rating: bool = False):
    # ... existing card display ...

    if enable_rating:
        with st.expander("📊 Rate This Sandwich"):
            rating_widget(sandwich, show_comparison=True)
```

**Impact:** Enables human validation research, creates unique dataset
**Time:** 8-10 hours

---

### 1.3 Fix Critical Bugs (Priority: CRITICAL)

**Issues:**
- N+1 query in Live Feed (calls `get_recent_sandwiches` twice)
- No error handling in `execute_query`
- Missing loading states
- No pagination total counts

**Tasks:**
- [ ] Cache sandwich data in session state to avoid duplicate queries
- [ ] Wrap `execute_query` in try/except with proper error handling
- [ ] Add `st.spinner()` to all slow operations
- [ ] Add total result counts to pagination

**Files to modify:**
- `pages/1_📊_Live_Feed.py`
- `pages/2_🔍_Browser.py`
- `dashboard/utils/db.py`

**Example fixes:**
```python
# pages/1_📊_Live_Feed.py - Fix N+1 query
@st.fragment(run_every="2s")
def live_feed():
    # Store in session state to avoid duplicate calls
    sandwiches = get_recent_sandwiches(limit=int(limit))
    st.session_state.last_sandwiches = sandwiches  # Cache for commentary section
    # ... rest of code ...

# At bottom, use cached data:
if 'last_sandwiches' in st.session_state and st.session_state.last_sandwiches:
    recent = st.session_state.last_sandwiches[0]
    if recent.get('reuben_commentary'):
        # ... show commentary ...

# dashboard/utils/db.py - Add error handling
def execute_query(query: str, params: tuple = None, fetch_one: bool = False):
    """Execute query with error handling."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            if fetch_one:
                return cur.fetchone()
            else:
                return cur.fetchall()
    except Exception as e:
        logger.error(f"Query failed: {query[:100]}... Error: {e}")
        raise
    finally:
        if conn:
            return_db_connection(conn)

# pages/2_🔍_Browser.py - Add loading state and total count
with st.spinner("Searching sandwiches..."):
    df = search_sandwiches(...)
    total_count = get_total_search_results(...)  # New query

st.write(f"Page {page + 1} of {(total_count + page_size - 1) // page_size}")
st.caption(f"Showing {page * page_size + 1}-{min((page + 1) * page_size, total_count)} of {total_count} results")
```

**Impact:** Better UX, prevents errors, clearer feedback
**Time:** 4-6 hours

---

## Phase 2: Statistical Rigor (Week 2) - HIGH PRIORITY

### 2.1 Enhanced Visualizations with Statistics

**Issue:** Charts lack statistical overlays, confidence intervals, significance testing

**Tasks:**
- [ ] Add mean/median lines to validity histogram
- [ ] Add confidence intervals to time series
- [ ] Add statistical annotations (μ, σ, skewness, kurtosis)
- [ ] Replace radar chart with parallel coordinates or grouped bar chart
- [ ] Add box plots for distribution comparison by structural type
- [ ] Add correlation heatmap for component scores

**Files to modify:**
- `pages/3_📈_Analytics.py`

**Enhanced Validity Distribution:**
```python
# pages/3_📈_Analytics.py
import numpy as np
from scipy import stats

def render_validity_distribution():
    validity_df = get_validity_distribution()

    if validity_df.empty:
        st.info("No validity data available yet.")
        return

    scores = validity_df['validity_score'].values

    # Calculate statistics
    mean = np.mean(scores)
    median = np.median(scores)
    std = np.std(scores)
    skewness = stats.skew(scores)
    kurtosis_val = stats.kurtosis(scores)

    # Create histogram
    fig = px.histogram(
        validity_df, x='validity_score', nbins=20,
        title="Validity Score Distribution",
        labels={'validity_score': 'Validity Score', 'count': 'Count'}
    )

    # Add statistical overlays
    fig.add_vline(
        x=mean, line_dash="dash", line_color="red",
        annotation_text=f"Mean: {mean:.2f}",
        annotation_position="top"
    )

    fig.add_vline(
        x=median, line_dash="dot", line_color="blue",
        annotation_text=f"Median: {median:.2f}",
        annotation_position="bottom"
    )

    # Add normal distribution overlay for comparison
    x_range = np.linspace(0, 1, 100)
    normal_dist = stats.norm.pdf(x_range, mean, std)
    # Scale to match histogram
    scale_factor = len(scores) * 0.05  # bin width
    normal_dist_scaled = normal_dist * scale_factor

    fig.add_trace(go.Scatter(
        x=x_range, y=normal_dist_scaled,
        mode='lines', name='Normal Distribution',
        line=dict(color='orange', dash='dash')
    ))

    fig.update_layout(height=400, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

    # Statistical summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Mean (μ)", f"{mean:.3f}")
    with col2:
        st.metric("Std Dev (σ)", f"{std:.3f}")
    with col3:
        st.metric("Skewness", f"{skewness:.3f}")
    with col4:
        st.metric("Kurtosis", f"{kurtosis_val:.3f}")
```

**Correlation Heatmap:**
```python
def render_correlation_matrix():
    """Show correlation between component scores."""
    st.subheader("Component Score Correlations")

    query = """
        SELECT
            bread_compat_score, containment_score,
            nontrivial_score, novelty_score, validity_score
        FROM sandwiches
        WHERE bread_compat_score IS NOT NULL
    """

    df = pd.DataFrame(execute_query(query))

    if df.empty:
        st.info("Not enough data for correlation analysis.")
        return

    # Calculate correlation matrix
    corr_matrix = df.corr()

    # Create heatmap
    fig = px.imshow(
        corr_matrix,
        labels=dict(color="Correlation"),
        x=['Bread', 'Contain', 'NonTriv', 'Novelty', 'Validity'],
        y=['Bread', 'Contain', 'NonTriv', 'Novelty', 'Validity'],
        color_continuous_scale='RdBu_r',
        zmin=-1, zmax=1,
        text_auto='.2f'
    )

    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Interpretation
    st.caption("""
    **Interpretation:** High correlation (>0.7) suggests redundancy.
    Low correlation (<0.3) indicates independent dimensions.
    """)
```

**Box Plot Comparison:**
```python
def render_type_comparison():
    """Box plots comparing validity across structural types."""
    st.subheader("Validity Distribution by Structural Type")

    query = """
        SELECT s.validity_score, st.name as structural_type
        FROM sandwiches s
        JOIN structural_types st ON s.structural_type_id = st.type_id
        WHERE s.validity_score IS NOT NULL
    """

    df = pd.DataFrame(execute_query(query))

    if df.empty:
        st.info("Not enough data for type comparison.")
        return

    fig = px.box(
        df, x='structural_type', y='validity_score',
        title="Validity Score Distribution by Type",
        labels={'validity_score': 'Validity Score', 'structural_type': 'Type'}
    )

    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Statistical testing
    st.markdown("**Statistical Tests:**")

    # ANOVA test
    groups = [group['validity_score'].values for name, group in df.groupby('structural_type')]
    f_stat, p_value = stats.f_oneway(*groups)

    if p_value < 0.05:
        st.success(f"✅ Significant difference detected (F={f_stat:.2f}, p={p_value:.4f})")
        st.caption("At least one structural type has significantly different validity scores.")
    else:
        st.info(f"No significant difference (F={f_stat:.2f}, p={p_value:.4f})")
```

**Impact:** Scientific credibility, reveals insights
**Time:** 10-12 hours

---

### 2.2 Human vs Reuben Analytics Page

**Issue:** No analysis of human rating data

**Tasks:**
- [ ] Create new analytics tab for human ratings
- [ ] Show aggregate agreement statistics
- [ ] Identify sandwiches with highest disagreement
- [ ] Calculate inter-rater reliability
- [ ] Show calibration analysis

**New file:**
- `pages/7_👥_Human_Ratings.py`

**Human Ratings Analytics:**
```python
# pages/7_👥_Human_Ratings.py
"""Human Ratings Analytics - Reuben vs Human Consensus"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from dashboard.utils.db import execute_query

st.set_page_config(page_title="Human Ratings", page_icon="👥", layout="wide")

st.title("👥 Human Ratings Analysis")
st.markdown("Compare Reuben's self-assessment with human consensus")

# Overall statistics
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_ratings = execute_query(
        "SELECT COUNT(*) as count FROM human_ratings",
        fetch_one=True
    )
    st.metric("Total Ratings", total_ratings['count'])

with col2:
    unique_sandwiches = execute_query(
        "SELECT COUNT(DISTINCT sandwich_id) as count FROM human_ratings",
        fetch_one=True
    )
    st.metric("Sandwiches Rated", unique_sandwiches['count'])

with col3:
    unique_raters = execute_query(
        "SELECT COUNT(DISTINCT session_id) as count FROM human_ratings",
        fetch_one=True
    )
    st.metric("Unique Raters", unique_raters['count'])

with col4:
    avg_agreement = execute_query("""
        SELECT AVG(ABS(s.validity_score - hr.avg_human)) as avg_diff
        FROM sandwiches s
        JOIN (
            SELECT sandwich_id, AVG(overall_validity) as avg_human
            FROM human_ratings
            GROUP BY sandwich_id
        ) hr ON s.sandwich_id = hr.sandwich_id
    """, fetch_one=True)
    agreement_pct = 100 - (avg_agreement['avg_diff'] * 100) if avg_agreement else 0
    st.metric("Agreement", f"{agreement_pct:.1f}%")

st.markdown("---")

# Scatter plot: Reuben vs Human
st.subheader("Reuben vs Human Consensus")

comparison_data = execute_query("""
    SELECT
        s.sandwich_id,
        s.name,
        s.validity_score as reuben_score,
        AVG(hr.overall_validity) as human_score,
        COUNT(hr.rating_id) as rating_count,
        st.name as structural_type
    FROM sandwiches s
    JOIN human_ratings hr ON s.sandwich_id = hr.sandwich_id
    JOIN structural_types st ON s.structural_type_id = st.type_id
    GROUP BY s.sandwich_id, s.name, s.validity_score, st.name
    HAVING COUNT(hr.rating_id) >= 3  -- At least 3 ratings
""")

if comparison_data:
    df = pd.DataFrame(comparison_data)

    fig = px.scatter(
        df, x='reuben_score', y='human_score',
        color='structural_type', size='rating_count',
        hover_data=['name'],
        title="Reuben's Score vs Human Consensus",
        labels={'reuben_score': "Reuben's Score", 'human_score': 'Human Consensus'}
    )

    # Add diagonal line (perfect agreement)
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1],
        mode='lines', name='Perfect Agreement',
        line=dict(color='gray', dash='dash')
    ))

    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

    # Correlation analysis
    correlation = df['reuben_score'].corr(df['human_score'])
    st.metric("Pearson Correlation", f"{correlation:.3f}")

    if correlation > 0.7:
        st.success("✅ Strong agreement between Reuben and humans!")
    elif correlation > 0.4:
        st.info("📊 Moderate agreement - some systematic differences exist.")
    else:
        st.warning("⚠️ Low agreement - Reuben's self-assessment may need calibration.")

    # Biggest disagreements
    st.markdown("---")
    st.subheader("Biggest Disagreements")

    df['disagreement'] = abs(df['reuben_score'] - df['human_score'])
    top_disagreements = df.nlargest(5, 'disagreement')

    for _, row in top_disagreements.iterrows():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.write(f"**{row['name']}**")
        with col2:
            st.write(f"🤖 {row['reuben_score']:.2f}")
        with col3:
            st.write(f"👥 {row['human_score']:.2f}")
        with col4:
            delta = row['human_score'] - row['reuben_score']
            st.write(f"Δ {delta:+.2f}")

else:
    st.info("Not enough human ratings yet. Need at least 3 ratings per sandwich for analysis.")

# Component-level analysis
st.markdown("---")
st.subheader("Component Score Analysis")

component_comparison = execute_query("""
    SELECT
        AVG(s.bread_compat_score) as reuben_bread,
        AVG(hr.bread_compat_score) as human_bread,
        AVG(s.containment_score) as reuben_contain,
        AVG(hr.containment_score) as human_contain,
        AVG(s.nontrivial_score) as reuben_nontrivial,
        AVG(hr.nontrivial_score) as human_nontrivial,
        AVG(s.novelty_score) as reuben_novelty,
        AVG(hr.novelty_score) as human_novelty
    FROM sandwiches s
    JOIN human_ratings hr ON s.sandwich_id = hr.sandwich_id
""", fetch_one=True)

if component_comparison:
    components = ['Bread Compat', 'Containment', 'Non-trivial', 'Novelty']
    reuben_scores = [
        component_comparison['reuben_bread'],
        component_comparison['reuben_contain'],
        component_comparison['reuben_nontrivial'],
        component_comparison['reuben_novelty']
    ]
    human_scores = [
        component_comparison['human_bread'],
        component_comparison['human_contain'],
        component_comparison['human_nontrivial'],
        component_comparison['human_novelty']
    ]

    fig = go.Figure(data=[
        go.Bar(name='Reuben', x=components, y=reuben_scores, marker_color='#ff6b9d'),
        go.Bar(name='Human', x=components, y=human_scores, marker_color='#4a90e2')
    ])

    fig.update_layout(barmode='group', height=400, yaxis_range=[0, 1])
    st.plotly_chart(fig, use_container_width=True)

    # Which component has biggest disagreement?
    differences = [abs(r - h) for r, h in zip(reuben_scores, human_scores)]
    max_diff_idx = differences.index(max(differences))

    st.caption(f"**Biggest disagreement:** {components[max_diff_idx]} (Δ {differences[max_diff_idx]:.2f})")
```

**Impact:** Unique research dataset, calibration insights
**Time:** 8-10 hours

---

## Phase 3: Advanced Analytics (Week 3) - MEDIUM PRIORITY

### 3.1 Network Graph Visualization

**Issue:** You have relationship data but never visualize it!

**Tasks:**
- [ ] Create interactive network graph
- [ ] Node sizing by validity score
- [ ] Edge width by similarity
- [ ] Community detection
- [ ] Centrality metrics

**New file:**
- `pages/4_🗺️_Network.py`

**Network visualization:**
```python
# pages/4_🗺️_Network.py
import streamlit as st
import networkx as nx
import plotly.graph_objects as go
from dashboard.utils.queries import get_sandwich_relations

st.set_page_config(page_title="Network", page_icon="🗺️", layout="wide")

st.title("🗺️ Sandwich Relationship Network")

# Filters
col1, col2 = st.columns(2)
with col1:
    min_similarity = st.slider("Min Similarity", 0.0, 1.0, 0.5, 0.05)
with col2:
    max_nodes = st.slider("Max Sandwiches", 10, 500, 100, 10)

# Get relationship data
relations = get_sandwich_relations(min_similarity, max_nodes)

if not relations:
    st.info("No relationships found. Try lowering the similarity threshold.")
else:
    # Build network graph
    G = nx.Graph()

    for rel in relations:
        G.add_edge(
            rel['sandwich1_id'],
            rel['sandwich2_id'],
            weight=rel['similarity_score']
        )

    # Calculate layout
    pos = nx.spring_layout(G, k=0.5, iterations=50)

    # Create edge traces
    edge_trace = []
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        weight = edge[2]['weight']

        edge_trace.append(go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode='lines',
            line=dict(width=weight*3, color='#ddd'),
            hoverinfo='none',
            showlegend=False
        ))

    # Create node trace
    node_x = []
    node_y = []
    node_text = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        # Get sandwich name
        sandwich = next((r for r in relations if r['sandwich1_id'] == node or r['sandwich2_id'] == node), None)
        node_text.append(sandwich['sandwich1_name'] if sandwich else str(node)[:8])

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        textposition="top center",
        marker=dict(
            size=10,
            color=list(dict(G.degree()).values()),
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Connections")
        ),
        hoverinfo='text'
    )

    # Create figure
    fig = go.Figure(data=edge_trace + [node_trace])
    fig.update_layout(
        showlegend=False,
        hovermode='closest',
        height=700,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Network statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Nodes", G.number_of_nodes())
    with col2:
        st.metric("Edges", G.number_of_edges())
    with col3:
        density = nx.density(G)
        st.metric("Density", f"{density:.3f}")
    with col4:
        if nx.is_connected(G):
            diameter = nx.diameter(G)
            st.metric("Diameter", diameter)
        else:
            components = nx.number_connected_components(G)
            st.metric("Components", components)
```

**Impact:** Visually impressive, reveals clustering patterns
**Time:** 6-8 hours

---

### 3.2 Anomaly Detection

**Issue:** No systematic identification of outliers

**Tasks:**
- [ ] Implement Z-score based outlier detection
- [ ] Flag sandwiches with unusual score patterns
- [ ] Identify temporal anomalies (unusual activity spikes)
- [ ] Create anomaly alerts page

**Add to Analytics page:**
```python
def detect_anomalies():
    """Detect statistical outliers in sandwich corpus."""
    st.subheader("Anomaly Detection")

    query = """
        SELECT sandwich_id, name, validity_score,
               bread_compat_score, containment_score,
               nontrivial_score, novelty_score
        FROM sandwiches
        WHERE validity_score IS NOT NULL
    """

    df = pd.DataFrame(execute_query(query))

    if df.empty:
        return

    # Z-score based outlier detection
    from scipy.stats import zscore

    df['validity_zscore'] = zscore(df['validity_score'])
    df['is_outlier'] = abs(df['validity_zscore']) > 2.5

    outliers = df[df['is_outlier']]

    if len(outliers) > 0:
        st.warning(f"⚠️ Found {len(outliers)} statistical outliers (|z| > 2.5)")

        for _, row in outliers.head(10).iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{row['name']}**")
            with col2:
                st.write(f"Score: {row['validity_score']:.2f}")
            with col3:
                st.write(f"Z-score: {row['validity_zscore']:.2f}")
    else:
        st.success("✅ No significant outliers detected")

    # Visualize outliers
    fig = px.scatter(
        df, x=df.index, y='validity_score',
        color='is_outlier',
        hover_data=['name'],
        title="Validity Scores with Outliers Highlighted"
    )

    st.plotly_chart(fig, use_container_width=True)
```

**Impact:** Identifies data quality issues, interesting edge cases
**Time:** 4-6 hours

---

### 3.3 Predictive Modeling

**Issue:** No forecasting or predictive features

**Tasks:**
- [ ] Time series forecasting (when will corpus reach 1000 sandwiches?)
- [ ] Predict sandwich quality from components
- [ ] Forecast foraging success rate
- [ ] Estimate API costs

**Add to Analytics:**
```python
def forecast_corpus_growth():
    """Forecast when corpus will reach milestones."""
    st.subheader("Corpus Growth Forecast")

    query = """
        SELECT DATE(created_at) as date, COUNT(*) as daily_count
        FROM sandwiches
        GROUP BY DATE(created_at)
        ORDER BY date
    """

    df = pd.DataFrame(execute_query(query))

    if len(df) < 7:
        st.info("Need at least 7 days of data for forecasting.")
        return

    # Simple linear regression forecast
    from sklearn.linear_model import LinearRegression

    df['day_num'] = range(len(df))
    X = df[['day_num']].values
    y = df['daily_count'].values

    model = LinearRegression()
    model.fit(X, y)

    # Forecast next 30 days
    future_days = np.arange(len(df), len(df) + 30).reshape(-1, 1)
    forecast = model.predict(future_days)

    # Calculate when we'll reach milestones
    current_total = execute_query("SELECT COUNT(*) as count FROM sandwiches", fetch_one=True)['count']
    daily_rate = model.coef_[0]

    milestones = [100, 500, 1000, 5000]

    st.markdown("**Estimated time to reach milestones:**")
    for milestone in milestones:
        if current_total >= milestone:
            st.success(f"✅ {milestone} sandwiches - Already achieved!")
        else:
            days_needed = (milestone - current_total) / daily_rate
            est_date = pd.Timestamp.now() + pd.Timedelta(days=days_needed)
            st.info(f"📅 {milestone} sandwiches - {est_date.strftime('%Y-%m-%d')} (~{int(days_needed)} days)")
```

**Impact:** Forward-looking insights, planning capability
**Time:** 6-8 hours

---

## Phase 4: Polish & Advanced Features (Week 4) - NICE TO HAVE

### 4.1 Full-Text Search Upgrade

**Replace ILIKE with proper full-text search:**
```python
# dashboard/utils/queries.py
def search_sandwiches_fulltext(query_text: str, ...):
    """Search using PostgreSQL full-text search."""
    sql = """
        SELECT s.*, st.name as structural_type,
               ts_rank(search_vector, plainto_tsquery('english', %s)) as rank
        FROM sandwiches s
        LEFT JOIN structural_types st ON s.structural_type_id = st.type_id
        WHERE search_vector @@ plainto_tsquery('english', %s)
        ORDER BY rank DESC, created_at DESC
        LIMIT %s OFFSET %s
    """
    # ... implementation
```

**Time:** 3-4 hours

---

### 4.2 Embedding-Based Clustering

**Use pgvector embeddings for semantic clustering:**
```python
def cluster_sandwiches():
    """Cluster sandwiches by embedding similarity."""
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA

    # Get embeddings
    query = """
        SELECT sandwich_id, name, filling_embedding::text
        FROM sandwiches
        WHERE filling_embedding IS NOT NULL
    """
    # Parse embeddings, run K-means, visualize with t-SNE
    # ... implementation
```

**Time:** 8-10 hours

---

### 4.3 Export & Collaboration Features

**Tasks:**
- [ ] Export publication-ready figures (high-res PNG, SVG)
- [ ] LaTeX table export for papers
- [ ] Annotation system (bookmark interesting sandwiches)
- [ ] Share filtered views via URL parameters

**Time:** 6-8 hours

---

## Priority Summary

### Must Do (Week 1) - 24-30 hours
1. Database indexes & schema (6-8h)
2. Human rating system (8-10h)
3. Fix critical bugs (4-6h)
4. Connection pooling (2h)

### Should Do (Week 2) - 24-30 hours
5. Statistical visualizations (10-12h)
6. Human ratings analytics (8-10h)
7. Error handling & loading states (4-6h)

### Nice to Have (Weeks 3-4) - 30-40 hours
8. Network graph (6-8h)
9. Anomaly detection (4-6h)
10. Predictive modeling (6-8h)
11. Full-text search (3-4h)
12. Clustering (8-10h)
13. Export features (6-8h)

---

## Success Metrics

After implementation, the dashboard should achieve:

✅ **Performance:** All queries < 500ms with 10k sandwiches
✅ **Research Value:** Human validation dataset with >100 ratings
✅ **Statistical Rigor:** All charts have confidence intervals, p-values
✅ **User Engagement:** 5+ ratings per sandwich on average
✅ **Code Quality:** 90%+ test coverage, no magic numbers
✅ **Scalability:** Handles 100k sandwiches without redesign

---

## Next Steps

1. **Review this plan** - Adjust priorities based on your goals
2. **Week 1 Focus** - Get database foundation + human ratings working
3. **Deploy incrementally** - Push changes to Streamlit Cloud weekly
4. **Gather feedback** - Monitor human rating engagement
5. **Iterate** - Adjust based on what users find valuable

Would you like me to start with Phase 1.1 (Database Schema) and Phase 1.2 (Human Rating System)?
