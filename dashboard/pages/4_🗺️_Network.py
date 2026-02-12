"""Network Graph Visualization - Sandwich Similarity Network

Interactive force-directed graph showing relationships between sandwiches
based on embedding similarity scores.
"""

import streamlit as st
import plotly.graph_objects as go
import networkx as nx
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add parent directory to path
project_root = Path(__file__).parent.parent
dashboard_dir = project_root / "dashboard"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(dashboard_dir))

from components.colors import COLORS
from utils.queries import get_sandwich_network_data

st.set_page_config(page_title="Network Graph", page_icon="🗺️", layout="wide")

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

st.title("🗺️ Sandwich Similarity Network")
st.markdown("Explore relationships between sandwiches based on embedding similarity")

st.markdown("---")

# Controls
col1, col2, col3 = st.columns(3)

with col1:
    min_similarity = st.slider(
        "Minimum Similarity",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.05,
        help="Only show edges with similarity above this threshold"
    )

with col2:
    max_nodes = st.slider(
        "Maximum Nodes",
        min_value=10,
        max_value=200,
        value=50,
        step=10,
        help="Limit number of sandwiches shown"
    )

with col3:
    layout_algorithm = st.selectbox(
        "Layout Algorithm",
        options=["spring", "kamada_kawai", "circular"],
        index=0,
        help="Algorithm for positioning nodes"
    )

st.markdown("---")

# Load network data
try:
    nodes_df, edges_df = get_sandwich_network_data(min_similarity=min_similarity, limit=max_nodes)

    if nodes_df.empty:
        st.info("📊 No sandwich data available. Create some sandwiches first!")
        st.stop()

    if edges_df.empty:
        st.warning(f"⚠️ No edges found with similarity ≥ {min_similarity:.2f}. Try lowering the threshold.")
        st.info(f"**Showing {len(nodes_df)} isolated nodes**")

        # Show nodes as a simple scatter plot if no edges
        fig = go.Figure()

        # Random positions for isolated nodes
        np.random.seed(42)
        x_pos = np.random.rand(len(nodes_df))
        y_pos = np.random.rand(len(nodes_df))

        fig.add_trace(go.Scatter(
            x=x_pos,
            y=y_pos,
            mode='markers',
            marker=dict(
                size=15,
                color=[COLORS.get(t, COLORS['accent']) for t in nodes_df['structural_type']],
                line=dict(width=2, color='white')
            ),
            text=nodes_df['name'],
            hovertemplate='<b>%{text}</b><br>Validity: %{customdata:.2f}<extra></extra>',
            customdata=nodes_df['validity_score']
        ))

        fig.update_layout(
            height=600,
            showlegend=False,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            hovermode='closest'
        )

        st.plotly_chart(fig, use_container_width=True)
        st.stop()

    # Build NetworkX graph
    G = nx.Graph()

    # Add nodes
    for _, row in nodes_df.iterrows():
        G.add_node(
            str(row['sandwich_id']),
            name=row['name'],
            validity=row['validity_score'],
            type=row['structural_type']
        )

    # Add edges
    for _, row in edges_df.iterrows():
        G.add_edge(
            str(row['sandwich_a']),
            str(row['sandwich_b']),
            weight=row['similarity_score']
        )

    # Remove isolated nodes
    G.remove_nodes_from(list(nx.isolates(G)))

    if len(G.nodes()) == 0:
        st.warning("⚠️ No connected nodes after filtering. Try lowering the similarity threshold.")
        st.stop()

    # Compute layout
    if layout_algorithm == "spring":
        pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)
    elif layout_algorithm == "kamada_kawai":
        pos = nx.kamada_kawai_layout(G)
    else:  # circular
        pos = nx.circular_layout(G)

    # Community detection
    try:
        from networkx.algorithms import community
        communities = community.greedy_modularity_communities(G)
        node_to_community = {}
        for i, comm in enumerate(communities):
            for node in comm:
                node_to_community[node] = i
    except Exception:
        # Fallback if community detection fails
        node_to_community = {node: 0 for node in G.nodes()}
        communities = [set(G.nodes())]

    # Calculate centrality metrics
    degree_centrality = nx.degree_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G)
    pagerank = nx.pagerank(G)

    # Create edges trace
    edge_x = []
    edge_y = []
    edge_widths = []

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_widths.append(G.edges[edge]['weight'] * 3)  # Scale width

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode='lines',
        line=dict(width=0.5, color='#888'),
        hoverinfo='none'
    )

    # Create nodes trace
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []
    node_hover = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        node_data = G.nodes[node]
        node_text.append(node_data['name'])

        # Color by community
        community_colors = ['#ff6b9d', '#4a90e2', '#2ecc71', '#f39c12', '#9b59b6', '#e74c3c']
        community_idx = node_to_community.get(node, 0)
        node_color.append(community_colors[community_idx % len(community_colors)])

        # Size by validity score
        node_size.append(node_data['validity'] * 30 + 10)

        # Hover text
        hover_text = f"""<b>{node_data['name']}</b><br>
Type: {node_data['type']}<br>
Validity: {node_data['validity']:.2f}<br>
Community: {community_idx + 1}<br>
Degree: {degree_centrality[node]:.3f}<br>
Betweenness: {betweenness_centrality[node]:.3f}<br>
PageRank: {pagerank[node]:.3f}"""
        node_hover.append(hover_text)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers',
        marker=dict(
            size=node_size,
            color=node_color,
            line=dict(width=2, color='white')
        ),
        text=node_text,
        hovertemplate='%{hovertext}<extra></extra>',
        hovertext=node_hover
    )

    # Create figure
    fig = go.Figure(data=[edge_trace, node_trace])

    fig.update_layout(
        title=f"Network: {len(G.nodes())} nodes, {len(G.edges())} edges, {len(communities)} communities",
        titlefont_size=16,
        showlegend=False,
        hovermode='closest',
        margin=dict(b=0, l=0, r=0, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

    # Network statistics
    st.markdown("---")
    st.subheader("📊 Network Statistics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Nodes", len(G.nodes()))

    with col2:
        st.metric("Edges", len(G.edges()))

    with col3:
        st.metric("Communities", len(communities))

    with col4:
        density = nx.density(G)
        st.metric("Density", f"{density:.3f}")

    # Top nodes by centrality
    st.markdown("---")
    st.subheader("🌟 Most Central Sandwiches")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**By Degree**")
        top_degree = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
        for node_id, score in top_degree:
            name = G.nodes[node_id]['name']
            st.caption(f"{name}: {score:.3f}")

    with col2:
        st.markdown("**By Betweenness**")
        top_between = sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
        for node_id, score in top_between:
            name = G.nodes[node_id]['name']
            st.caption(f"{name}: {score:.3f}")

    with col3:
        st.markdown("**By PageRank**")
        top_pagerank = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:5]
        for node_id, score in top_pagerank:
            name = G.nodes[node_id]['name']
            st.caption(f"{name}: {score:.3f}")

except Exception as e:
    st.error(f"Error loading network graph: {e}")
    import traceback
    st.code(traceback.format_exc())

# Footer with explanation
st.markdown("---")
with st.expander("💡 Understanding the Network Graph"):
    st.markdown("""
    ### What Am I Looking At?

    **Nodes (circles):** Each node represents a sandwich
    - Size = validity score (bigger = more valid)
    - Color = community membership (similar sandwiches cluster together)

    **Edges (lines):** Connections show similarity above the threshold
    - Based on embedding similarity from the LLM

    **Communities:** Detected using greedy modularity algorithm
    - Sandwiches with similar characteristics group together

    ### Centrality Metrics

    **Degree Centrality:** How many connections a sandwich has
    - High degree = well-connected sandwich

    **Betweenness Centrality:** How often a sandwich lies on paths between others
    - High betweenness = "bridge" between communities

    **PageRank:** Importance based on connections to other important sandwiches
    - High PageRank = influential sandwich

    ### Layout Algorithms

    - **Spring:** Physics-based (nodes repel, edges attract)
    - **Kamada-Kawai:** Minimizes total energy
    - **Circular:** Arranges nodes in a circle
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #999; padding: 1rem;'>
    <p style='font-size: 0.9rem; font-style: italic;'>
        🌺 "Look at how the sandwiches form communities. It's like a little sandwich society." — Sandy
    </p>
</div>
""", unsafe_allow_html=True)
