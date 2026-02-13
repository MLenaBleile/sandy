"""Creator page.

About MaryLena Bleile, Sandy's creator.
"""

import streamlit as st
import sys
import base64
from pathlib import Path

# Add project root and dashboard to path
project_root = Path(__file__).parent.parent
dashboard_dir = project_root / "dashboard"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(dashboard_dir))

st.set_page_config(page_title="Creator", page_icon="👩\u200d💻", layout="wide")

# Consistent styling
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #fff5e6 0%, #ffe6f0 100%);
    }
    h1 { color: #ff6b9d; text-shadow: 2px 2px 4px rgba(255, 182, 193, 0.3); }
    h2, h3 { color: #ff8fab; }
    a { color: #ff6b9d; }
    a:hover { color: #ff8fab; }
</style>
""", unsafe_allow_html=True)

# Sandy intro
try:
    from components.sandy_mascot import render_sandy_speaking
    render_sandy_speaking(
        "This is the human who built me. She's alright, I guess. Makes decent sandwiches for a non-cube.",
        size=80,
    )
except ImportError:
    pass

st.markdown("---")

# ============================================================
# Photo + Bio layout
# ============================================================

# Load and encode the image for inline HTML (avoids Streamlit static file path issues)
photo_path = dashboard_dir / "static" / "creator.png"
photo_html = ""
if photo_path.exists():
    img_bytes = photo_path.read_bytes()
    img_b64 = base64.b64encode(img_bytes).decode()
    photo_html = f"""
    <img src="data:image/png;base64,{img_b64}"
         alt="MaryLena Bleile"
         style="width: 220px; border-radius: 14px; box-shadow: 0 4px 15px rgba(255,107,157,0.25);" />
    """

col_photo, col_bio = st.columns([1, 2.5])

with col_photo:
    if photo_html:
        st.markdown(photo_html, unsafe_allow_html=True)
    st.markdown("")

with col_bio:
    st.markdown("## MaryLena Bleile, Ph.D.")

    st.markdown("""
    Canadian statistician based in New York City. Sandy's creator.

    MaryLena works at the intersection of **Causal Inference** and **Reinforcement Learning**,
    with a background in Bayesian and mixed models. She has previously worked as a biomarker study
    statistician at **Sanofi**, in the Epi/Bio department at **Memorial Sloan Kettering Cancer Center**,
    and in the AI and Automation lab at **UT Southwestern Medical Center**.

    Outside of work, she trains **Brazilian Jiu-Jitsu** and **Judo** and regularly lifts weights at the gym.
    """)

st.markdown("---")

# ============================================================
# The Book
# ============================================================
st.markdown("### The Book")

st.markdown("""
<div style="
    background: linear-gradient(135deg, #f8f4ff 0%, #fff0f5 100%);
    border: 2px solid #e8d5f5;
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin: 0.5rem 0 1.5rem;
">
    <h4 style="color: #9b59b6; margin-top: 0;">Optimal Control Using Causal Agents</h4>
    <p style="color: #777; font-style: italic; margin-bottom: 0.8rem;">
        Translational Synergies in Causal Inference and Reinforcement Learning
    </p>
    <p style="color: #555; font-size: 0.95rem;">
        A translation manual bridging 70 years of parallel mathematical development in
        Causal Inference and Reinforcement Learning. Written for researchers and practitioners
        already familiar with either field, it builds bridges between existing concepts rather
        than constructing them from the ground up.
    </p>
    <p style="color: #555; font-size: 0.95rem;">
        Topics include clinical decision-making, Brazilian Jiu-Jitsu strategy optimization,
        GARCH financial modeling, non-Markovian dynamics, and missing data challenges.
        Implementations in both R and Python.
    </p>
    <p style="color: #888; font-size: 0.85rem; margin-bottom: 0;">
        <b>Publisher:</b> CRC Press (Chapman & Hall) &nbsp;|&nbsp;
        <b>Status:</b> Forthcoming
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown(
    "**[causal-rl-bridges.com](https://www.causal-rl-bridges.com)** "
    "— book site with chapter previews and code"
)

st.markdown("---")

# ============================================================
# Links
# ============================================================
st.markdown("### Links")

link_cols = st.columns(4)

links = [
    ("🌐", "Personal Site", "https://www.marylenableile.com"),
    ("📖", "Book Site", "https://www.causal-rl-bridges.com"),
    ("💻", "GitHub", "https://github.com/MLenaBleile"),
    ("🔬", "Google Scholar", "https://scholar.google.com/citations?user=eCPQzR8AAAAJ"),
]

for i, (icon, label, url) in enumerate(links):
    with link_cols[i]:
        st.markdown(f"""
        <a href="{url}" target="_blank" style="text-decoration: none;">
            <div style="
                background: white;
                border: 2px solid #f0d0e0;
                border-radius: 12px;
                padding: 1rem;
                text-align: center;
                transition: transform 0.2s, box-shadow 0.2s;
            "
            onmouseover="this.style.transform='scale(1.03)'; this.style.boxShadow='0 4px 12px rgba(255,107,157,0.2)';"
            onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='none';"
            >
                <div style="font-size: 1.8rem;">{icon}</div>
                <div style="color: #ff6b9d; font-weight: 600; font-size: 0.9rem;">{label}</div>
            </div>
        </a>
        """, unsafe_allow_html=True)

st.markdown("")

# ============================================================
# LinkedIn CTA
# ============================================================
st.markdown("---")

st.markdown("""
<div style="
    text-align: center;
    padding: 1.5rem;
    background: linear-gradient(135deg, #f0f7ff 0%, #fff0f5 100%);
    border-radius: 16px;
    margin: 0.5rem 0;
">
    <p style="font-size: 1.1rem; color: #555; margin-bottom: 0.8rem;">
        Interested in causal inference, reinforcement learning, or AI agents that make sandwiches?
    </p>
    <a href="https://www.linkedin.com/in/marylena-bleile-bb7b33132/" target="_blank" style="
        display: inline-block;
        background: #0077B5;
        color: white;
        font-size: 1rem;
        font-weight: 600;
        padding: 0.6rem 1.8rem;
        border-radius: 25px;
        text-decoration: none;
        box-shadow: 0 4px 12px rgba(0,119,181,0.3);
        transition: transform 0.2s;
    "
    onmouseover="this.style.transform='scale(1.05)';"
    onmouseout="this.style.transform='scale(1)';"
    >Connect on LinkedIn</a>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #999; padding: 0.5rem; font-style: italic;'>
    "I could solve any problem in the universe. But have you considered: a nice Reuben?"
</div>
""", unsafe_allow_html=True)
