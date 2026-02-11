"""Interactive Sandwich Maker - Chat with Sandy!

Let Sandy make sandwiches from your URLs or topics in real-time.
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path to import dashboard modules
dashboard_dir = Path(__file__).parent.parent
sys.path.insert(0, str(dashboard_dir))

# Add project root to import sandwich modules
project_root = dashboard_dir.parent
sys.path.insert(0, str(project_root / "src"))

from components.sandwich_card import sandwich_card
from utils.db import get_connection

st.set_page_config(page_title="Make a Sandwich", page_icon="🎨", layout="wide")

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
    .stTextInput > div > div > input {
        border: 2px solid #ffb6c1;
        border-radius: 10px;
    }
    .stButton > button {
        background: linear-gradient(135deg, #ff6b9d 0%, #ff8fab 100%);
        color: white;
        border: none;
        border-radius: 20px;
        padding: 10px 30px;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(255, 107, 157, 0.3);
    }
    .stButton > button:hover {
        box-shadow: 0 6px 8px rgba(255, 107, 157, 0.4);
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

st.title("🎨 Make a Sandwich with Sandy!")

st.markdown("""
<p style='font-size: 1.2rem; color: #666; font-style: italic;'>
    Give Sandy a URL or topic, and watch as it creates a conceptual sandwich in real-time! ✨
</p>
""", unsafe_allow_html=True)

# Initialize session state
if 'sandwich_made' not in st.session_state:
    st.session_state.sandwich_made = None
if 'making_sandwich' not in st.session_state:
    st.session_state.making_sandwich = False

# Input section
st.markdown("### 📝 What should Sandy make a sandwich about?")

col1, col2 = st.columns([3, 1])

with col1:
    user_input = st.text_input(
        "Enter a URL or topic",
        placeholder="e.g., https://en.wikipedia.org/wiki/Biomimicry or 'quantum computing'",
        label_visibility="collapsed"
    )

with col2:
    make_button = st.button("🥪 Make Sandwich", use_container_width=True)

# Help text
st.markdown("""
<p style='font-size: 0.9rem; color: #888;'>
    💡 <b>Tips:</b> Give Sandy a URL to analyze, or just a topic/concept and Sandy will think about it!
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# Handle sandwich making
if make_button and user_input:
    st.session_state.making_sandwich = True
    st.session_state.sandwich_made = None

    # Create progress container
    progress_container = st.container()

    with progress_container:
        st.markdown("### 🔮 Sandy is working...")

        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Import Sandy's pipeline
            from sandwich.agent.pipeline import make_sandwich, SourceMetadata, PipelineConfig
            from sandwich.db.corpus import SandwichCorpus
            from sandwich.db.repository import Repository
            from sandwich.llm.gemini import GeminiSandwichLLM
            from sandwich.llm.embeddings import OpenAIEmbeddingService
            from sandwich.db.models import Source, Sandwich
            import asyncio
            import hashlib
            from datetime import datetime

            # Setup
            status_text.text("🔧 Initializing Sandy...")
            progress_bar.progress(10)

            # Get API keys from Streamlit secrets
            gemini_key = st.secrets.get("GEMINI_API_KEY")
            openai_key = st.secrets.get("OPENAI_API_KEY")

            if not gemini_key or not openai_key:
                st.error("⚠️ Missing API keys in Streamlit secrets!")
                st.info("Please add GEMINI_API_KEY and OPENAI_API_KEY to Streamlit secrets.")
                st.stop()

            # Initialize services (using Gemini for free tier!)
            llm = GeminiSandwichLLM(api_key=gemini_key)
            embeddings = OpenAIEmbeddingService(api_key=openai_key)

            # Get database connection
            conn = get_connection()
            repo = Repository(conn)

            # Load corpus
            corpus = SandwichCorpus()
            sandwiches = repo.get_all_sandwiches()
            for s in sandwiches:
                emb = repo.get_sandwich_embeddings(s.sandwich_id)
                if emb:
                    corpus.add_sandwich(emb, s.structural_type_id or 0)
            corpus.total_sandwiches = len(sandwiches)

            progress_bar.progress(20)

            # Determine if input is URL or topic
            status_text.text("📥 Fetching content...")
            if user_input.startswith(('http://', 'https://')):
                # Fetch URL content
                import requests
                from urllib.parse import urlparse

                try:
                    response = requests.get(user_input, timeout=15)
                    response.raise_for_status()
                    content = response.text
                    parsed = urlparse(user_input)
                    source_metadata = SourceMetadata(
                        url=user_input,
                        domain=parsed.netloc,
                        content_type='html'
                    )
                except Exception as e:
                    st.error(f"Failed to fetch URL: {e}")
                    st.stop()
            else:
                # Use topic as content
                content = user_input
                source_metadata = SourceMetadata(
                    url=None,
                    domain=None,
                    content_type='text'
                )

            progress_bar.progress(35)
            status_text.text("🔍 Sandy is analyzing the content...")

            # Run the pipeline
            async def run_pipeline():
                return await make_sandwich(
                    content=content,
                    source_metadata=source_metadata,
                    corpus=corpus,
                    llm=llm,
                    embeddings=embeddings,
                    config=PipelineConfig()
                )

            stored_sandwich, outcome = asyncio.run(run_pipeline())

            progress_bar.progress(80)

            if not stored_sandwich:
                st.warning(f"😕 Sandy couldn't make a sandwich: {outcome.detail}")
                st.info(f"Stage: {outcome.stage}, Outcome: {outcome.outcome}")
                st.stop()

            # Save to database
            status_text.text("💾 Saving to database...")

            # Insert source
            content_hash = hashlib.sha256(
                (source_metadata.url or "").encode()
            ).hexdigest()[:16]

            source = Source(
                url=source_metadata.url,
                domain=source_metadata.domain,
                content_type=source_metadata.content_type,
                content_hash=content_hash,
            )
            source_id = repo.insert_source(source)

            # Look up structural type ID
            type_cache = {}
            sw = stored_sandwich.assembled
            v = stored_sandwich.validation

            type_id = type_cache.get(sw.structure_type)
            if type_id is None:
                st_type = repo.get_structural_type_by_name(sw.structure_type)
                if st_type and st_type.type_id:
                    type_id = st_type.type_id
                    type_cache[sw.structure_type] = type_id

            # Insert sandwich
            sandwich = Sandwich(
                sandwich_id=stored_sandwich.sandwich_id,
                name=sw.name,
                description=sw.description,
                bread_top=sw.bread_top,
                bread_bottom=sw.bread_bottom,
                filling=sw.filling,
                validity_score=v.overall_score,
                bread_compat_score=v.bread_compat_score,
                containment_score=v.containment_score,
                specificity_score=v.specificity_score,
                nontrivial_score=v.nontrivial_score,
                novelty_score=v.novelty_score,
                source_id=source_id,
                structural_type_id=type_id,
                assembly_rationale=sw.containment_argument,
                validation_rationale=v.rationale,
                sandy_commentary=sw.sandy_commentary,
            )
            repo.insert_sandwich(sandwich)

            # Store embeddings
            repo.insert_sandwich_embeddings(
                stored_sandwich.sandwich_id,
                stored_sandwich.embeddings.full
            )

            progress_bar.progress(100)
            status_text.text("🎉 Sandwich created!")

            # Store in session state for display
            st.session_state.sandwich_made = {
                'sandwich_id': str(stored_sandwich.sandwich_id),
                'name': sw.name,
                'validity_score': v.overall_score,
                'bread_top': sw.bread_top,
                'filling': sw.filling,
                'bread_bottom': sw.bread_bottom,
                'description': sw.description,
                'sandy_commentary': sw.sandy_commentary,
                'bread_compat_score': v.bread_compat_score,
                'containment_score': v.containment_score,
                'nontrivial_score': v.nontrivial_score,
                'novelty_score': v.novelty_score,
                'structural_type': sw.structure_type,
                'created_at': datetime.now()
            }

            st.session_state.making_sandwich = False

            # Clear progress
            progress_container.empty()

        except Exception as e:
            st.error(f"❌ Error creating sandwich: {e}")
            import traceback
            st.code(traceback.format_exc())
            st.session_state.making_sandwich = False

# Display created sandwich
if st.session_state.sandwich_made:
    st.markdown("### 🎉 Your Fresh Sandwich!")
    st.balloons()

    sandwich_card(st.session_state.sandwich_made)

    st.markdown("---")
    st.markdown("### ✨ Make Another?")
    if st.button("🔄 Clear and Make Another Sandwich"):
        st.session_state.sandwich_made = None
        st.rerun()

# Show example inputs
if not st.session_state.sandwich_made and not st.session_state.making_sandwich:
    st.markdown("### 💡 Example Topics to Try")

    examples = [
        "🌿 Biomimicry in design",
        "🔬 Quantum entanglement",
        "🎨 The philosophy of minimalism",
        "🚀 Space exploration ethics",
        "🧠 Neuroplasticity",
        "https://en.wikipedia.org/wiki/Systems_thinking"
    ]

    cols = st.columns(3)
    for idx, example in enumerate(examples):
        with cols[idx % 3]:
            if st.button(example, key=f"example_{idx}", use_container_width=True):
                st.session_state.example_input = example.split(" ", 1)[1] if example.startswith(("🌿", "🔬", "🎨", "🚀", "🧠")) else example
                st.rerun()

# Handle example click
if 'example_input' in st.session_state:
    user_input = st.session_state.example_input
    del st.session_state.example_input
