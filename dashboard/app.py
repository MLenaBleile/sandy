"""Main Streamlit dashboard for Sandy.

Landing page with Sandy character theming from Lilo & Stitch!
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
    page_title="Sandy's Kitchen 🥪",
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
    """Main dashboard landing page with Sandy theming."""

    # Cute sidebar header
    st.sidebar.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <div style='font-size: 3rem;'>🥪</div>
        <h2 style='color: #ff6b9d; margin: 0.5rem 0;'>SANDY</h2>
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
    **Explore Sandy's creations:**
    - 🎨 **Make Sandwich** - Create one yourself!
    - 📊 **Live Feed** - Fresh sandwiches
    - 🔍 **Browser** - Search the corpus
    - 📈 **Analytics** - See the stats
    - ⚙️ **Settings** - Configure & export
    """)

    # Fun footer in sidebar
    st.sidebar.markdown("---")
    st.sidebar.caption("🌺 Inspired by Experiment 625")

    # Page title
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0 0.5rem;'>
        <h1 style='font-size: 3rem; margin: 0;'>🥪 Welcome to Sandy's Kitchen! 🥪</h1>
    </div>
    """, unsafe_allow_html=True)

    # Sandy mascot with speech bubble
    try:
        from components.sandy_mascot import render_sandy_speaking
        render_sandy_speaking(
            "The universe is vast. Somewhere in it: bread.",
            size=110,
        )
    except ImportError:
        st.markdown("""
        <div style='text-align: center; padding: 0.5rem 0;'>
            <p style='font-size: 1.1rem; color: #666; font-style: italic;'>
                "The universe is vast. Somewhere in it: bread."
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Big prominent CTA to Make Sandwich
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0 1.5rem;'>
        <a href="/Make_Sandwich" target="_self" style='
            display: inline-block;
            background: linear-gradient(135deg, #ffd700 0%, #ff6b9d 100%);
            color: white;
            font-size: 1.5rem;
            font-weight: 700;
            padding: 0.8rem 2.5rem;
            border-radius: 30px;
            text-decoration: none;
            box-shadow: 0 6px 20px rgba(255, 107, 157, 0.4);
            transition: transform 0.2s, box-shadow 0.2s;
            letter-spacing: 0.5px;
        '
        onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='0 8px 25px rgba(255,107,157,0.55)';"
        onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='0 6px 20px rgba(255,107,157,0.4)';"
        >🎨 Make a Sandwich</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Fun introduction
    st.markdown("""
    ### 👋 What is this place?

    Sandy is an AI agent who, with all the knowledge in the world available, chooses to spend his time making sandwiches. Sandy is inspired by Experiment 625 in Lilo and Stitch, a super-powerful alien who wasn't useful to the scientest because he only wanted to make sandwiches.

    Each sandwich has:
    - 🍞 **Two pieces of bread** (related concepts that bound something)
    - 🥓 **A filling** (the thing being bounded)
    - ⭐ **A quality score** (how good the sandwich is)
    """)

    st.markdown("---")

    # Quick stats
    st.markdown("### 📊 Kitchen Stats")
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
        st.error(f"Couldn't load metrics: {e}")
        st.info("🔧 Make sure the database is initialized!")

    # Example sandwiches
    st.markdown("### 🌟 Example Sandwiches")

    col1, col2 = st.columns(2)

    with col1:
        st.info("""
        **The Dark Side of the Force** 🎬
        - 🍞 Jedi Order's rigid discipline
        - 🥓 Anakin's fall to the dark side
        - 🍞 The Sith's seductive freedom

        *"The turn only happens because both philosophies exist as extremes."*
        """)

    with col2:
        st.success("""
        **The Taylor Swift Discography** 🎵
        - 🍞 Country roots (*Tim McGraw*)
        - 🥓 The genre pivot (*1989*, *Reputation*)
        - 🍞 Indie/folk reinvention (*Folklore*)

        *"Both breads are 'authentic Taylor' — the pop era is bounded by sincerity."*
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
    with st.expander("🌺 About Sandy & The SANDWICH Project"):
        st.markdown("""
        ### Who is Sandy?

        Sandy is an AI sandwich-making agent inspired by Experiment 625 from Disney's *Lilo & Stitch* —
        a character who has vast powers but chooses to make sandwiches instead. This captures the spirit
        of our project: **capability constrained by aesthetic choice**.

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
        <p>🌺 Built with Streamlit & Love | Powered by Gemini 🤖</p>
        <p style='font-size: 0.9rem; font-style: italic;'>
            "The internet is vast. Somewhere in it: bread." — Sandy
        </p>
        <p style='font-size: 0.8rem; margin-top: 0.5rem;'>
            Created by <a href="https://www.marylenableile.com" target="_blank" style="color: #ff8fab; text-decoration: none;">Mary Lena Bleile</a>
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
