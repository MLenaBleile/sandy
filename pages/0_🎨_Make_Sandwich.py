"""Interactive Sandwich Maker - Chat with Sandy!

Let Sandy make sandwiches from your URLs or topics in real-time.
"""

import streamlit as st
import sys
import random
from pathlib import Path

# Add project root and dashboard to path
project_root = Path(__file__).parent.parent
dashboard_dir = project_root / "dashboard"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(dashboard_dir))
sys.path.insert(0, str(project_root / "src"))

try:
    from components.sandwich_card import sandwich_card
    from components.sandy_mascot import render_sandy, render_sandy_speaking, get_commentary
    from utils.db import get_db_connection
except ImportError as e:
    st.error(f"Import error: {e}")
    st.info("This page requires the full sandwich codebase to be available.")
    st.stop()

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
    Give Sandy a URL or topic, and watch as a conceptual sandwich gets created in real-time! ✨
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
        # Sandy mascot + speech bubble area
        sandy_bubble = st.empty()
        progress_bar = st.progress(0)

        def update_sandy(stage: str, progress: int, custom_msg: str = None):
            """Update Sandy's speech bubble and progress bar."""
            msg = custom_msg or get_commentary(stage, random.randint(0, 10))
            sandy_bubble.markdown("", unsafe_allow_html=True)  # clear
            with sandy_bubble.container():
                render_sandy_speaking(msg, size=100)
            progress_bar.progress(progress)

        try:
            # Import Sandy's pipeline
            try:
                from sandwich.agent.pipeline import make_sandwich, SourceMetadata, PipelineConfig
                from sandwich.db.corpus import SandwichCorpus
                from sandwich.db.repository import Repository
                from sandwich.llm.gemini import GeminiSandwichLLM
                from sandwich.llm.gemini_embeddings import GeminiEmbeddingService
                from sandwich.db.models import Source, Sandwich
                import asyncio
                import hashlib
                from datetime import datetime
            except ImportError as e:
                st.error(f"Failed to import sandwich modules: {e}")
                st.info("Make sure all dependencies are installed: google-generativeai, anthropic, openai")
                raise

            # Stage: Init
            update_sandy("init", 10)

            # Get API keys from Streamlit secrets
            gemini_key = st.secrets.get("GEMINI_API_KEY")
            openai_key = st.secrets.get("OPENAI_API_KEY")

            if not gemini_key:
                st.error("⚠️ Missing GEMINI_API_KEY in Streamlit secrets!")
                st.info("Please add GEMINI_API_KEY to Streamlit secrets.")
                st.info("Get your free key at: https://aistudio.google.com/apikey")
                st.stop()

            # Initialize LLM (using Gemini - free!)
            llm = GeminiSandwichLLM(api_key=gemini_key)

            # Initialize embeddings
            if openai_key:
                from sandwich.llm.embeddings import OpenAIEmbeddingService
                from sandwich.config import LLMConfig; config = LLMConfig(openai_api_key=openai_key); embeddings = OpenAIEmbeddingService(config=config)
            else:
                st.warning("⚠️ No OPENAI_API_KEY found. Using Gemini embeddings (may not match existing corpus).")
                embeddings = GeminiEmbeddingService(api_key=gemini_key)

            # Get database connection
            database_url = st.secrets["DATABASE_URL"]
            repo = Repository(database_url)

            # Load corpus
            corpus = SandwichCorpus()
            sandwiches = repo.get_all_sandwiches()
            for s in sandwiches:
                emb = repo.get_sandwich_embeddings(s.sandwich_id)
                if emb:
                    corpus.add_sandwich(emb, s.structural_type_id or 0)
            corpus.total_sandwiches = len(sandwiches)

            update_sandy("init", 15, "Kitchen is ready. Let's see what we're working with...")

            # Stage: Fetch content
            update_sandy("fetch", 20)

            if user_input.startswith(('http://', 'https://')):
                import requests
                from urllib.parse import urlparse

                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    response = requests.get(user_input, timeout=15, headers=headers)
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
                content = user_input
                source_metadata = SourceMetadata(
                    url=None,
                    domain=None,
                    content_type='text'
                )

            update_sandy("fetch", 30, "Got the ingredients. Now let me find the bread...")

            # Stage: Identify + Select + Assemble + Validate (pipeline)
            update_sandy("identify", 40)

            async def run_pipeline():
                return await make_sandwich(
                    content=content,
                    source_metadata=source_metadata,
                    corpus=corpus,
                    llm=llm,
                    embeddings=embeddings,
                    config=PipelineConfig()
                )

            # Run pipeline in background thread so we can update Sandy while waiting
            import threading, time

            pipeline_result = {"sandwich": None, "outcome": None, "error": None, "done": False}

            def run_pipeline_thread():
                try:
                    s, o = asyncio.run(run_pipeline())
                    pipeline_result["sandwich"] = s
                    pipeline_result["outcome"] = o
                except Exception as e:
                    pipeline_result["error"] = e
                finally:
                    pipeline_result["done"] = True

            thread = threading.Thread(target=run_pipeline_thread, daemon=True)
            thread.start()

            # Cycle Sandy's commentary while pipeline runs
            pipeline_quips = [
                "Analyzing the structure... looking for bounded patterns...",
                "Hmm, interesting material here...",
                "I see some potential bread candidates...",
                "Let me look at this from another angle...",
                "Separating the wheat from the chaff. Literally.",
                "The bread must relate independently of the filling!",
                "Checking if these concepts bound something meaningful...",
                "Constructing something beautiful here...",
                "The containment argument is key. Trust me on this.",
                "Almost there... just need to find the right filling...",
                "Every great sandwich tells a story.",
                "Is that a filling I spot? Let me look closer...",
                "Quality takes time. Good sandwiches can't be rushed.",
                "Bread on top... filling in the middle... bread on the bottom. Classic.",
                "Let me taste-test this... metaphorically.",
            ]
            quip_idx = 0
            stages = ["identify", "assemble", "validate"]

            while not pipeline_result["done"]:
                stage = stages[min(quip_idx // 5, len(stages) - 1)]
                progress = min(45 + quip_idx * 3, 80)
                update_sandy(stage, progress, pipeline_quips[quip_idx % len(pipeline_quips)])
                quip_idx += 1
                time.sleep(2.5)

            thread.join()

            if pipeline_result["error"]:
                raise pipeline_result["error"]

            stored_sandwich = pipeline_result["sandwich"]
            outcome = pipeline_result["outcome"]

            if not stored_sandwich:
                update_sandy("identify", 50, f"Hmm, couldn't make a sandwich: {outcome.detail}")
                st.warning(f"😕 Sandy couldn't make a sandwich: {outcome.detail}")
                st.info(f"Stage: {outcome.stage}, Outcome: {outcome.outcome}")
                st.stop()

            # Stage: Save
            update_sandy("save", 85, "That's a good one! Let me save it...")

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

            update_sandy("save", 92, "Saving embeddings... almost there!")

            # Store embeddings
            repo.update_sandwich_embeddings(
                stored_sandwich.sandwich_id,
                bread_top_emb=stored_sandwich.embeddings.bread_top,
                bread_bottom_emb=stored_sandwich.embeddings.bread_bottom,
                filling_emb=stored_sandwich.embeddings.filling,
                sandwich_emb=stored_sandwich.embeddings.full,
            )

            # Clear the progress area — celebration Sandy will take over below
            progress_bar.progress(100)

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

            # Clear progress area so celebration Sandy is the only one
            sandy_bubble.empty()
            progress_bar.empty()

        except Exception as e:
            st.error(f"❌ Error creating sandwich: {e}")
            import traceback
            st.code(traceback.format_exc())
            st.session_state.making_sandwich = False

# Display created sandwich
if st.session_state.sandwich_made:
    st.markdown("### 🎉 Your Fresh Sandwich!")
    st.balloons()

    # Show Sandy celebrating
    render_sandy_speaking(
        f"I call this one <b>{st.session_state.sandwich_made['name']}</b>. "
        f"Scored {st.session_state.sandwich_made['validity_score']:.2f} — not bad!",
        size=80
    )

    st.markdown("")
    sandwich_card(st.session_state.sandwich_made)

    st.markdown("---")
    st.markdown("### ✨ Make Another?")
    if st.button("🔄 Clear and Make Another Sandwich"):
        st.session_state.sandwich_made = None
        st.rerun()

# Show example inputs
if not st.session_state.sandwich_made and not st.session_state.making_sandwich:
    # Show Sandy in idle state
    render_sandy_speaking("Give me a topic or URL and I'll make you a sandwich!", size=80)

    st.markdown("")
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
