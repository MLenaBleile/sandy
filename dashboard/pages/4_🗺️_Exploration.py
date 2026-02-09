"""Sandwich Exploration Map page.

Network visualization of sandwich relationships.
"""

import streamlit as st
import plotly.graph_objects as go
import networkx as nx
import sys
from pathlib import Path

# Add parent directory to path
dashboard_dir = Path(__file__).parent.parent
sys.path.insert(0, str(dashboard_dir))

from components.colors import COLORS, get_structural_type_color
from utils.queries import get_recent_sandwiches, get_sandwich_relations

st.set_page_config(page_title="Exploration", page_icon="🗺️", layout="wide")

st.title("🗺️ Sandwich Exploration Map")

st.markdown("Visualize relationships between sandwiches as an interactive network graph.")

# Controls
col1, col2 = st.columns([3, 1])

with col1:
    search_query = st.text_input(
        "🔎 Search",
        placeholder="Search for sandwich names to highlight...",
        key="exploration_search"
    )

with col2:
    limit = st.number_input(
        "Max Nodes",
        min_value=10,
        max_value=500,
        value=100,
        step=10,
        help="Limit graph to N most recent sandwiches"
    )

similarity_threshold = st.slider(
    "Similarity Threshold",
    min_value=0.0,
    max_value=1.0,
    value=0.7,
    step=0.05,
    help="Minimum similarity score to show edge"
)

st.markdown("---")


@st.cache_data(ttl=60)
def build_sandwich_graph(node_limit: int, sim_threshold: float):
    """Build NetworkX graph from sandwich data.

    Args:
        node_limit: Maximum number of nodes
        sim_threshold: Minimum similarity for edges

    Returns:
        Tuple of (Graph, positions dict)
    """
    G = nx.Graph()

    # Add nodes (sandwiches)
    sandwiches = get_recent_sandwiches(limit=node_limit)

    for s in sandwiches:
        G.add_node(
            str(s['sandwich_id']),
            label=s['name'],
            validity=s.get('validity_score', 0.0),
            type=s.get('structural_type', 'unknown')
        )

    # Add edges (relations)
    relations = get_sandwich_relations(similarity_threshold=sim_threshold, limit=1000)

    for rel in relations:
        # Only add edge if both nodes exist
        if str(rel['sandwich_a']) in G.nodes and str(rel['sandwich_b']) in G.nodes:
            G.add_edge(
                str(rel['sandwich_a']),
                str(rel['sandwich_b']),
                weight=rel['similarity_score']
            )

    # Compute layout (spring layout for force-directed)
    if len(G.nodes) > 0:
        pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)
    else:
        pos = {}

    return G, pos


try:
    G, pos = build_sandwich_graph(int(limit), similarity_threshold)

    if len(G.nodes) == 0:
        st.info("No sandwiches available for graph. Create some sandwiches first!")
        st.code("python -m sandwich.main --max-sandwiches 10", language="bash")
    else:
        # Create Plotly figure
        edge_trace = go.Scatter(
            x=[],
            y=[],
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )

        # Add edges
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace['x'] += (x0, x1, None)
            edge_trace['y'] += (y0, y1, None)

        # Add nodes
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        node_sizes = []

        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

            node_data = G.nodes[node]
            node_text.append(node_data['label'])

            # Color by structural type
            node_colors.append(get_structural_type_color(node_data['type']))

            # Size by validity score
            node_sizes.append(10 + node_data['validity'] * 20)

        # Highlight searched nodes
        highlight_mask = []
        if search_query:
            for text in node_text:
                highlight_mask.append(search_query.lower() in text.lower())
        else:
            highlight_mask = [False] * len(node_text)

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers',
            hoverinfo='text',
            text=node_text,
            marker=dict(
                showscale=False,
                color=node_colors,
                size=node_sizes,
                line=dict(
                    width=[3 if h else 0 for h in highlight_mask],
                    color='#FFD700'  # Gold highlight
                )
            )
        )

        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace])

        fig.update_layout(
            title=f"Sandwich Network ({len(G.nodes)} nodes, {len(G.edges)} edges)",
            showlegend=False,
            hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=600
        )

        st.plotly_chart(fig, use_container_width=True)

        # Graph stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Nodes", len(G.nodes))

        with col2:
            st.metric("Edges", len(G.edges))

        with col3:
            density = nx.density(G) if len(G.nodes) > 1 else 0.0
            st.metric("Density", f"{density:.3f}")

        with col4:
            if len(G.nodes) > 0 and len(G.edges) > 0:
                avg_degree = sum(dict(G.degree()).values()) / len(G.nodes)
                st.metric("Avg Degree", f"{avg_degree:.1f}")
            else:
                st.metric("Avg Degree", "0.0")

        # Legend
        st.markdown("---")
        st.markdown("**Legend:**")
        st.markdown("- **Node size** = Validity score")
        st.markdown("- **Node color** = Structural type")
        st.markdown("- **Edge** = Similarity relationship")
        st.markdown("- **Gold outline** = Matches search query")

except Exception as e:
    st.error(f"Error building graph: {e}")
    import traceback
    st.code(traceback.format_exc())
