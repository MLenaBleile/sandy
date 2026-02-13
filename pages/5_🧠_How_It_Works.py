"""How It Works page.

Explains Sandy's multi-agent architecture, pipeline, and tech stack.
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root and dashboard to path
project_root = Path(__file__).parent.parent
dashboard_dir = project_root / "dashboard"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(dashboard_dir))

st.set_page_config(page_title="How It Works", page_icon="🧠", layout="wide")

# Consistent styling
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #fff5e6 0%, #ffe6f0 100%);
    }
    h1 { color: #ff6b9d; text-shadow: 2px 2px 4px rgba(255, 182, 193, 0.3); }
    h2, h3 { color: #ff8fab; }
</style>
""", unsafe_allow_html=True)

# Sandy greeting
try:
    from components.sandy_mascot import render_sandy_speaking
    render_sandy_speaking(
        "Want to see how I'm built? Pull up a chair.",
        size=80,
    )
except ImportError:
    pass

st.markdown("---")

# ============================================================
# The Big Picture
# ============================================================
st.markdown("### The Big Picture")

st.markdown("""
Sandy takes any content — a URL, a topic, a PDF — and finds **conceptual sandwiches** hidden in it.
A sandwich is a structure where two related concepts (bread) meaningfully bound a third concept (filling).

The entire process is orchestrated by a **multi-agent pipeline** where specialized agents handle
each stage of sandwich-making. Every agent has a single job and does it well.
""")

# ============================================================
# Pipeline Architecture
# ============================================================
st.markdown("### The Pipeline")

st.markdown("""
<div style="
    background: linear-gradient(135deg, #f8f4ff 0%, #fff0f5 100%);
    border: 2px solid #e8d5f5;
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin: 1rem 0;
    font-family: monospace;
    font-size: 0.85rem;
    line-height: 1.8;
    color: #444;
    overflow-x: auto;
">
<b style="color:#ff6b9d;">Input</b> (URL, topic, file)
  &darr;
<b style="color:#9b59b6;">Preprocessor</b> &mdash; clean HTML, extract text, language check, quality filter
  &darr;
<b style="color:#3498db;">Identifier</b> &mdash; LLM finds candidate bread pairs + fillings
  &darr;
<b style="color:#2ecc71;">Selector</b> &mdash; pick best candidate using novelty + confidence scoring
  &darr;
<b style="color:#e67e22;">Assembler</b> &mdash; LLM builds the full sandwich (name, description, containment argument)
  &darr;
<b style="color:#e74c3c;">Validator</b> &mdash; LLM scores on 5 dimensions, rejects if below threshold
  &darr;
<b style="color:#1abc9c;">Embeddings</b> &mdash; encode bread, filling, and full sandwich into vector space
  &darr;
<b style="color:#ff6b9d;">Repository</b> &mdash; store in PostgreSQL with pgvector for similarity search
</div>
""", unsafe_allow_html=True)

st.markdown("")

# ============================================================
# Agent Details
# ============================================================
st.markdown("### The Agents")

agents = [
    {
        "icon": "🧹",
        "name": "Preprocessor",
        "file": "preprocessor.py",
        "desc": "Strips HTML tags, navigation, ads, and boilerplate. Detects language "
                "(English only for now). Filters content that's too short, too noisy, or "
                "too low-quality to contain meaningful structure. Ensures the downstream "
                "agents get clean, substantive text to work with.",
    },
    {
        "icon": "🔬",
        "name": "Identifier",
        "file": "identifier.py",
        "desc": "The most creative agent. Given cleaned text, it uses a large language model "
                "to find candidate sandwich structures — pairs of related concepts that could "
                "serve as bread, with something meaningful between them. Returns multiple "
                "candidates ranked by confidence.",
    },
    {
        "icon": "🎯",
        "name": "Selector",
        "file": "selector.py",
        "desc": "Picks the best candidate from the Identifier's output. Checks novelty against "
                "the existing sandwich corpus using embedding similarity — Sandy won't make the "
                "same sandwich twice. Balances confidence with novelty to find the most "
                "interesting viable candidate.",
    },
    {
        "icon": "🏗️",
        "name": "Assembler",
        "file": "assembler.py",
        "desc": "Takes the selected candidate and builds a complete sandwich. Uses an LLM to "
                "generate a creative name, a description explaining the structure, a containment "
                "argument (why the filling is bounded by the bread), and Sandy's personal commentary.",
    },
    {
        "icon": "✅",
        "name": "Validator",
        "file": "validator.py",
        "desc": "The quality gate. Scores every sandwich on five dimensions: bread compatibility, "
                "containment, specificity, non-triviality, and novelty. Each dimension gets a 0-1 "
                "score from an LLM judge. Sandwiches below 0.70 overall are rejected. Sandy has standards.",
    },
]

cols = st.columns(len(agents))
for i, agent in enumerate(agents):
    with cols[i]:
        st.markdown(f"""
        <div style="
            background: white;
            border: 2px solid #f0d0e0;
            border-radius: 14px;
            padding: 1.2rem;
            text-align: center;
            min-height: 280px;
        ">
            <div style="font-size: 2rem;">{agent['icon']}</div>
            <h4 style="color: #ff6b9d; margin: 0.3rem 0;">{agent['name']}</h4>
            <code style="font-size: 0.7rem; color: #999;">{agent['file']}</code>
            <p style="font-size: 0.82rem; color: #555; margin-top: 0.5rem; text-align: left;">
                {agent['desc']}
            </p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("")

# ============================================================
# Validation Scoring
# ============================================================
st.markdown("### Validation Scoring")

st.markdown("""
Every sandwich Sandy makes is scored on five dimensions. The weighted average determines
whether it's good enough to keep.
""")

scoring = [
    ("🍞 Bread Compatibility", "0.20", "Are both breads the same type of thing? Are they related to each other *before* you introduce the filling?"),
    ("📦 Containment", "0.25", "Is the filling genuinely bounded by the bread? Does it emerge from the relationship between them?"),
    ("🎯 Specificity", "0.20", "Are the ingredients concrete and nameable, not vague abstractions like 'nature' or 'society'?"),
    ("💡 Non-triviality", "0.15", "Is this more than a tautology or restatement? Does it reveal something non-obvious?"),
    ("✨ Novelty", "0.20", "How distinct is this from sandwiches Sandy has already made? Checked via embedding similarity."),
]

for dim, weight, desc in scoring:
    st.markdown(f"**{dim}** (weight: {weight}) — {desc}")

st.markdown("")
st.info("**Rejection threshold: 0.70** — Sandy won't keep a sandwich he's not proud of.")

st.markdown("---")

# ============================================================
# The Three Structural Constraints
# ============================================================
st.markdown("### The Three Structural Constraints")

st.markdown("""
Through iterative development, we discovered three critical constraints that distinguish valid
sandwiches from superficially plausible ones:
""")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
    <div style="background: #fff0f5; border-radius: 12px; padding: 1rem; min-height: 200px;">
        <h4 style="color: #e74c3c;">1. Specificity</h4>
        <p style="font-size: 0.85rem; color: #555;">
            Ingredients must be concrete, not vague abstractions.<br><br>
            &#10060; "Nature as source"<br>
            &#9989; "Gecko setae adhesion mechanism"
        </p>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div style="background: #f0f5ff; border-radius: 12px; padding: 1rem; min-height: 200px;">
        <h4 style="color: #3498db;">2. Structural Homology</h4>
        <p style="font-size: 0.85rem; color: #555;">
            Both breads must be the same kind of thing.<br><br>
            &#10060; "Mechanism" / "Application"<br>
            &#9989; "Prior P(&theta;)" / "Likelihood P(D|&theta;)"
        </p>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div style="background: #f0fff5; border-radius: 12px; padding: 1rem; min-height: 200px;">
        <h4 style="color: #2ecc71;">3. Independent Bread</h4>
        <p style="font-size: 0.85rem; color: #555;">
            The breads must relate <em>before</em> you introduce the filling.<br><br>
            <b>The Bread Test:</b> Can you explain how the breads relate WITHOUT mentioning the filling?
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# Tech Stack
# ============================================================
st.markdown("### Tech Stack")

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("""
    **LLM Providers**
    - **Gemini 2.5 Flash** — default for sandwich making (fast, cheap)
    - **Claude** (Anthropic) — available via BYOK
    - **OpenAI** — embeddings only (text-embedding-3-small)

    **Database**
    - **PostgreSQL** with **pgvector** extension
    - Hosted on **Neon** (serverless Postgres)
    - Vector similarity search for novelty checking

    **Frontend**
    - **Streamlit** — dashboard and interactive sandwich maker
    - Custom SVG mascot with CSS animations
    - Hosted on **Streamlit Cloud**
    """)

with col_right:
    st.markdown("""
    **Pipeline Architecture**
    - **Python 3.11+** async pipeline
    - 5 specialized agents, each with a single responsibility
    - LLM calls for identification, assembly, and validation
    - Embedding-based novelty detection against the full corpus

    **Key Libraries**
    - `google-generativeai` — Gemini API
    - `anthropic` — Claude API
    - `openai` — embeddings
    - `sqlalchemy` — ORM
    - `pdfplumber` — PDF extraction
    - `beautifulsoup4` — HTML parsing

    **Input Sources**
    - URLs (any webpage)
    - Plain text topics (via DuckDuckGo search)
    - PDF and CSV file uploads
    """)

st.markdown("---")

# ============================================================
# Sandwich Taxonomy
# ============================================================
st.markdown("### Sandwich Taxonomy")

st.markdown("Sandy recognizes (and discovers) structural types:")

taxonomy = {
    "Bound": ("Upper/lower limits", "Bounded quantity", "Squeeze theorem"),
    "Dialectic": ("Thesis/antithesis", "Synthesis", "Hegelian triad"),
    "Epistemic": ("Assumption/evidence", "Conclusion", "Scientific method"),
    "Temporal": ("Before/after", "Transition", "Historical narrative"),
    "Stochastic": ("Prior/likelihood", "Posterior", "Bayesian inference"),
    "Optimization": ("Constraints", "Optimum", "Linear programming"),
    "Negotiation": ("Position A/B", "Compromise", "Treaty negotiations"),
}

import pandas as pd
tax_df = pd.DataFrame([
    {"Type": t, "Bread Relation": r, "Filling Role": f, "Example": e}
    for t, (r, f, e) in taxonomy.items()
])
st.dataframe(tax_df, use_container_width=True, hide_index=True)

st.markdown("---")

# ============================================================
# Source Code
# ============================================================
st.markdown("### Source Code")

st.markdown("""
Sandy is open source. The full codebase — pipeline, agents, prompts, dashboard, and tests — is on GitHub.

[**github.com/MLenaBleile/sandy**](https://github.com/MLenaBleile/sandy)
""")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #999; padding: 0.5rem; font-style: italic;'>
    "They ask why I make sandwiches. But have they asked why the sandwich makes itself?"
</div>
""", unsafe_allow_html=True)
