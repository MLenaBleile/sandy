"""Main Streamlit dashboard for Reuben.

Landing page with Reuben character theming from Lilo & Stitch!
"""

import streamlit as st
import os
from pathlib import Path

# Import utilities
from utils.db import check_database_connection
from utils.queries import (
    get_total_sandwich_count,
    get_avg_validity,
    get_sandwiches_today
)

# Configure page with cute branding
st.set_page_config(
    page_title="Reuben's Kitchen 🥪",
    page_icon="🥪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
css_file = Path(__file__).parent / "static" / "styles.css"
if css_file.exists():
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Add cute header styling
st.markdown("""
<style>
    /* Cute pastel color scheme */
    .main {
        background: linear-gradient(135deg, #fff5e6 0%, #ffe6f0 100%);
    }

    /* Metric cards with cute styling */
    [data-testid="stMetricValue"] {
        color: #ff6b9d;
        font-size: 2.5rem;
        font-weight: 700;
    }

    /* Sidebar with warm colors */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #fff9e6 0%, #ffe6e6 100%);
    }

    /* Cute buttons */
    .stButton>button {
        background: linear-gradient(135deg, #ffd700 0%, #ff6b9d 100%);
        color: white;
        border-radius: 20px;
        border: none;
        font-weight: 600;
        padding: 0.5rem 2rem;
        transition: transform 0.2s;
    }

    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(255, 107, 157, 0.4);
    }

    /* Cute headers */
    h1 {
        color: #ff6b9d;
        text-shadow: 2px 2px 4px rgba(255, 182, 193, 0.3);
    }

    h2, h3 {
        color: #ff8fab;
    }
</style>
""", unsafe_allow_html=True)


def render_system_status():
    """Display system health in sidebar with cute styling."""
    st.sidebar.markdown("### 🔧 System Status")

    db_healthy = check_database_connection()
    agent_healthy = True  # Stubbed

    # Cute status indicators
    if db_healthy:
        st.sidebar.success("✨ Database Connected!")
    else:
        st.sidebar.error("💔 Database Disconnected")

    if agent_healthy:
        st.sidebar.info("🤖 Agent Ready!")
    else:
        st.sidebar.warning("😴 Agent Sleeping")


def main():
    """Main dashboard landing page with Reuben theming."""

    # Cute sidebar header
    st.sidebar.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <div style='font-size: 3rem;'>🥪</div>
        <h2 style='color: #ff6b9d; margin: 0.5rem 0;'>REUBEN</h2>
        <p style='color: #999; font-size: 0.9rem; font-style: italic;'>
            "I could make sandwiches!"
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("---")

    render_system_status()

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### 🎯 Navigation
    **Explore Reuben's creations:**
    - 📊 **Live Feed** - Fresh sandwiches!
    - 🔍 **Browser** - Search the corpus
    - 📈 **Analytics** - See the stats
    - 🗺️ **Exploration** - Connection map
    - ✨ **Interactive** - Make one yourself
    - ⚙️ **Settings** - Configure & export
    """)

    # Fun footer in sidebar
    st.sidebar.markdown("---")
    st.sidebar.caption("🌺 Experiment 625 at your service!")

    # Main content with cute header
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 3rem; margin: 0;'>🥪 Welcome to Reuben's Kitchen! 🥪</h1>
        <p style='font-size: 1.2rem; color: #666; font-style: italic; margin-top: 0.5rem;'>
            "The internet is vast. Somewhere in it: bread."
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Quick stats with cute styling
    try:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total = get_total_sandwich_count()
            st.metric("🥪 Total Sandwiches", total)

        with col2:
            avg = get_avg_validity()
            st.metric("⭐ Avg Quality", f"{avg:.2f}")

        with col3:
            st.metric("🎯 Active Session", "Resting 😴")

        with col4:
            today = get_sandwiches_today()
            st.metric("🌟 Made Today", today)

    except Exception as e:
        st.error(f"Ohana means family! But I can't load metrics: {e}")
        st.info("🔧 Make sure the database is initialized!")

    st.markdown("---")

    # Fun introduction
    st.markdown("""
    ### 👋 What is this place?

    Reuben (Experiment 625 from Lilo & Stitch) is an AI agent who **only makes sandwiches**.
    Not just any sandwiches — **knowledge sandwiches**!

    Each sandwich has:
    - 🍞 **Two pieces of bread** (related concepts that bound something)
    - 🥓 **A filling** (the thing being bounded)
    - ⭐ **A quality score** (how good the sandwich is)
    """)

    # Example sandwiches
    st.markdown("### 🌟 Example Sandwiches")

    col1, col2 = st.columns(2)

    with col1:
        st.info("""
        **The Squeeze Theorem** 🎓
        - 🍞 Upper bound g(x)
        - 🥓 Target function f(x)
        - 🍞 Lower bound h(x)

        *"The filling does not choose its fate. It is determined by the bread."*
        """)

    with col2:
        st.success("""
        **The Bayesian BLT** 📊
        - 🍞 Prior distribution
        - 🥓 Posterior distribution
        - 🍞 Likelihood function

        *"Always fresh, always constrained by what came before."*
        """)

    st.markdown("---")

    # Getting started guide with cute styling
    st.markdown("### 🚀 Getting Started")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **🔬 For Researchers:**
        1. 📊 Check the **Live Feed** for recent creations
        2. 🔍 Use **Browser** to search sandwiches
        3. 📈 Dive into **Analytics** for patterns
        4. 💾 **Export** your findings
        """)

    with col2:
        st.markdown("""
        **👨‍💻 For Developers:**
        1. ✅ Monitor **System Status** in sidebar
        2. 📊 Watch **Analytics** for quality metrics
        3. 🗺️ Explore **Relationships** between sandwiches
        4. ⚙️ Configure in **Settings**
        """)

    st.markdown("---")

    # About section
    with st.expander("🌺 About Reuben & The SANDWICH Project"):
        st.markdown("""
        ### Who is Reuben?

        Reuben is **Experiment 625** from Disney's *Lilo & Stitch*. He has all of Stitch's powers
        but chooses to make sandwiches instead. This captures the spirit of our project:
        **capability constrained by aesthetic choice**.

        ### What is SANDWICH?

        **S**tructured **A**utonomous **N**avigation and **D**iscovery **W**ith **I**ntelligent
        **C**ontent **H**armonization — an AI agent that explores the internet and constructs
        "sandwiches" of knowledge.

        ### Why Sandwiches?

        The sandwich is the simplest non-trivial bounded structure. It requires:
        - Two related elements (bread compatibility)
        - A third element meaningfully constrained by the first two (containment)
        - Non-degeneracy (the filling must be distinct)

        This pattern appears everywhere:
        - 📐 Mathematics: bounds, inequalities, limits
        - 💬 Rhetoric: thesis-antithesis-synthesis
        - 🤝 Negotiation: positions bracketing compromise
        - 🧠 Philosophy: assumptions constraining conclusions

        ### The Philosophy

        *"They ask why I make sandwiches. But have they asked why the sandwich makes itself?
        In all things: bread, filling, bread. The universe is hungry for structure."*
        """)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #999; padding: 1rem;'>
        <p>🌺 Built with Streamlit & Love | Powered by Claude Sonnet 4.5 🤖</p>
        <p style='font-size: 0.9rem; font-style: italic;'>
            "Ohana means family. Family means nobody gets left behind.
            But if you want a sandwich, I got you covered." — Reuben
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
