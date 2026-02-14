"""Interactive Sandwich Maker - Chat with Sandy!

Let Sandy make sandwiches from your URLs, topics, or uploaded files in real-time.
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
    from components.sandy_mascot import (
        render_sandy_speaking, get_commentary, get_error_commentary,
        render_sandy_animated, render_speech_bubble,
    )
    from utils.db import get_db_connection
except ImportError as e:
    st.error(f"Import error: {e}")
    st.info("This page requires the full sandwich codebase to be available.")
    st.stop()

st.set_page_config(page_title="Make a Sandwich", page_icon="🎨", layout="wide")

# ---- Sidebar: Bring Your Own API Key ----
with st.sidebar:
    st.markdown("### 🔑 API Key")
    st.markdown(
        "<p style='font-size:0.85rem;color:#888;'>"
        "Use your own API key to avoid shared rate limits.</p>",
        unsafe_allow_html=True,
    )
    _provider_choice = st.selectbox(
        "Provider",
        ["Gemini (default)", "Claude (Anthropic)"],
        index=0,
        help="Which LLM provider to use for sandwich making.",
    )
    _user_key_input = st.text_input(
        "API Key",
        type="password",
        placeholder="Paste your key...",
        label_visibility="collapsed",
        help="Stored only in your browser session. Never saved to disk.",
    )
    # Store in session state
    st.session_state.user_api_key = _user_key_input.strip() if _user_key_input else ""
    st.session_state.user_provider = _provider_choice

    if st.session_state.user_api_key:
        st.success("Using your key", icon="✅")
    else:
        st.caption("Using shared Gemini key (may hit rate limits)")

    # Provider-specific link to get a key
    _key_links = {
        "Gemini (default)": "[Get a free Gemini key ↗](https://aistudio.google.com/apikey)",
        "Claude (Anthropic)": "[Get a Claude key ↗](https://console.anthropic.com/settings/keys)",
    }
    st.markdown(_key_links.get(_provider_choice, ""))
    st.divider()

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

# Initialize session state
if 'sandwich_made' not in st.session_state:
    st.session_state.sandwich_made = None
if 'making_sandwich' not in st.session_state:
    st.session_state.making_sandwich = False
if 'existing_matches' not in st.session_state:
    st.session_state.existing_matches = None

# ============================================================
# Single Sandy slot — only ONE Sandy visible at any time
# ============================================================
sandy_slot = st.empty()

# Show greeting Sandy (will be replaced when making starts or result shows)
if not st.session_state.making_sandwich and not st.session_state.sandwich_made:
    with sandy_slot.container():
        render_sandy_speaking("Give me a topic or URL and I'll make you a sandwich!", size=80)

# ============================================================
# Input area
# ============================================================
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
    💡 <b>Tips:</b> Paste a URL, type a topic (Sandy will search for it!), or upload a file below.<br>
    🌐 <b>Pro tip:</b> Wikipedia links work best! Try pasting a Wikipedia article about your favorite movie, band, or historical event.
</p>
""", unsafe_allow_html=True)

# File upload section
st.markdown("""
<p style='font-size: 0.9rem; color: #aaa; text-align: center; margin: 4px 0;'>
    — or upload a file —
</p>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Upload a PDF or CSV file",
    type=["pdf", "csv"],
    label_visibility="collapsed",
    help="Sandy can extract sandwich material from PDFs and CSV files!",
)

st.markdown("---")


# ============================================================
# Multi-topic helpers
# ============================================================
import re as _re


def _split_multi_topic(text: str) -> list:
    """Detect and split multi-topic input into individual topic strings."""
    text = text.strip()

    separators = [
        r'\s+and\s+',
        r'\s*&\s*',
        r'\s*\+\s*',
        r'\s+vs\.?\s+',
        r'\s*,\s*',
    ]

    for sep in separators:
        parts = _re.split(sep, text, flags=_re.IGNORECASE)
        parts = [p.strip() for p in parts if p.strip()]
        if len(parts) >= 2:
            return parts[:3]

    return [text]


def _search_and_fetch_topic(topic: str, headers: dict, max_chars: int = 5000):
    """Search DuckDuckGo for a single topic and extract plain text."""
    import requests as _req
    from bs4 import BeautifulSoup as _BS

    try:
        search_resp = _req.post(
            "https://html.duckduckgo.com/html/",
            data={"q": topic},
            headers=headers,
            timeout=15,
        )
        search_resp.raise_for_status()

        soup = _BS(search_resp.text, "html.parser")
        result_links = (
            soup.select("a.result__a")
            or soup.select("a.result-link")
            or soup.select(".result a[href^='http']")
        )

        if not result_links:
            result_links = [
                a for a in soup.select("a[href^='http']")
                if 'duckduckgo' not in (a.get('href', ''))
            ]

        search_url = None
        for link in result_links[:5]:
            href = link.get("href", "")
            if href and href.startswith("http") and "duckduckgo" not in href:
                search_url = href
                break

        if not search_url:
            return None, None

        page_resp = _req.get(search_url, headers=headers, timeout=15)
        page_resp.raise_for_status()

        page_soup = _BS(page_resp.text, "html.parser")
        for tag in page_soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()
        text = page_soup.get_text(separator="\n", strip=True)

        return text[:max_chars], search_url

    except Exception:
        return None, None


# ============================================================
# Check for existing sandwiches before making a new one
# ============================================================
def _check_existing_sandwiches(query_text: str, source_url: str = None) -> list:
    """Search the DB broadly for sandwiches matching this topic or source URL."""
    try:
        from utils.db import execute_query

        # Search across name, description, bread, filling, commentary, AND source URL
        sql = """
            SELECT
                s.sandwich_id, s.name, s.validity_score,
                s.bread_top, s.filling, s.bread_bottom,
                s.description, s.sandy_commentary,
                s.bread_compat_score, s.containment_score,
                s.nontrivial_score, s.novelty_score,
                s.created_at,
                st.name as structural_type,
                src.domain as source_domain,
                src.url as source_url
            FROM sandwiches s
            LEFT JOIN structural_types st ON s.structural_type_id = st.type_id
            LEFT JOIN sources src ON s.source_id = src.source_id
            WHERE (
                s.name ILIKE %s
                OR s.description ILIKE %s
                OR s.bread_top ILIKE %s
                OR s.bread_bottom ILIKE %s
                OR s.filling ILIKE %s
                OR s.sandy_commentary ILIKE %s
        """
        pattern = f"%{query_text}%"
        params = [pattern, pattern, pattern, pattern, pattern, pattern]

        # Also match by source URL if provided
        if source_url:
            sql += " OR src.url = %s"
            params.append(source_url)

        sql += """
            )
            ORDER BY s.validity_score DESC
            LIMIT 5
        """

        results = execute_query(sql, tuple(params))
        return results if results else []
    except Exception:
        pass
    return []

# Show existing matches if we found some (user hasn't clicked "Make New Anyway" yet)
_force_make = False
if st.session_state.existing_matches:
    with sandy_slot.container():
        render_sandy_speaking(
            f"I've already made sandwiches about this! Check them out below, "
            f"or I can make a brand new one.",
            size=80,
        )

    st.markdown("### 🥪 Existing Sandwiches on This Topic")
    for match in st.session_state.existing_matches:
        sandwich_card(match)

    st.markdown("")
    col_new, col_clear = st.columns([1, 1])
    with col_new:
        if st.button("🆕 Make a New One Anyway", use_container_width=True):
            _force_make = True
            st.session_state.existing_matches = None
    with col_clear:
        if st.button("👍 These are good, never mind", use_container_width=True):
            st.session_state.existing_matches = None
            st.rerun()

# ============================================================
# Handle sandwich making
# ============================================================
if (make_button or _force_make) and (user_input or uploaded_file):
    # Check for duplicates first (unless forcing)
    if make_button and not _force_make and user_input and not uploaded_file:
        _raw_input = user_input.strip()
        _source_url = None

        if _raw_input.startswith(("http://", "https://")):
            _source_url = _raw_input  # exact URL match
            # Also extract readable text for ILIKE search
            if "/wiki/" in _raw_input:
                _search_term = _raw_input.split("/wiki/")[-1].replace("_", " ").replace("(", "").replace(")", "")
            else:
                from urllib.parse import urlparse as _up
                _search_term = _up(_raw_input).netloc
        else:
            _search_term = _raw_input

        existing = _check_existing_sandwiches(_search_term, source_url=_source_url)
        if existing:
            st.session_state.existing_matches = existing
            st.rerun()

    st.session_state.making_sandwich = True
    st.session_state.sandwich_made = None
    st.session_state.existing_matches = None

    # Replace greeting Sandy with progress Sandy + speech bubble
    with sandy_slot.container():
        sandy_col, bubble_col = st.columns([1, 3])
        with sandy_col:
            render_sandy_animated(size=100)
        with bubble_col:
            bubble_slot = st.empty()

    progress_bar = st.progress(0)

    def update_sandy(stage: str, progress: int, custom_msg: str = None):
        """Update Sandy's speech bubble and progress bar."""
        msg = custom_msg or get_commentary(stage, random.randint(0, 10))
        with bubble_slot.container():
            render_speech_bubble(msg)
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

        # Resolve API key: user's own key takes priority over shared default
        user_key = st.session_state.get("user_api_key", "")
        provider = st.session_state.get("user_provider", "Gemini (default)")
        default_gemini_key = st.secrets.get("GEMINI_API_KEY")

        if user_key and "Claude" in provider:
            from sandwich.llm.anthropic import AnthropicSandwichLLM
            import os
            os.environ["ANTHROPIC_API_KEY"] = user_key
            llm = AnthropicSandwichLLM()
            gemini_key = default_gemini_key
        elif user_key and "Gemini" in provider:
            gemini_key = user_key
            llm = GeminiSandwichLLM(api_key=gemini_key)
        else:
            gemini_key = default_gemini_key
            if not gemini_key:
                st.error("⚠️ No API key available!")
                st.info("Paste your own key in the **sidebar**, or add GEMINI_API_KEY to Streamlit secrets.")
                st.info("Get your free key at: https://aistudio.google.com/apikey")
                st.stop()
            llm = GeminiSandwichLLM(api_key=gemini_key)

        # Initialize embeddings (OpenAI — matches existing corpus)
        openai_key = st.secrets.get("OPENAI_API_KEY")
        if openai_key:
            import os as _os
            _os.environ["OPENAI_API_KEY"] = openai_key
            from sandwich.llm.embeddings import OpenAIEmbeddingService
            embeddings = OpenAIEmbeddingService()
        elif gemini_key:
            embeddings = GeminiEmbeddingService(api_key=gemini_key)
        else:
            st.warning("⚠️ No API key available for embeddings.")
            embeddings = GeminiEmbeddingService(api_key="")

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

        # ============================================================
        # Input routing: file upload → URL → web search
        # ============================================================
        content = None
        source_metadata = None

        if uploaded_file is not None:
            # --- FILE UPLOAD ---
            file_ext = uploaded_file.name.rsplit(".", 1)[-1].lower() if "." in uploaded_file.name else ""

            if file_ext == "pdf":
                update_sandy("fetch", 20, get_error_commentary("upload_pdf"))
                try:
                    import pdfplumber

                    uploaded_file.seek(0)

                    pdf_text_parts = []
                    with pdfplumber.open(uploaded_file) as pdf:
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                pdf_text_parts.append(page_text)

                    content = "\n\n".join(pdf_text_parts)

                    if not content.strip():
                        msg = get_error_commentary("upload_empty")
                        update_sandy("fetch", 20, msg)
                        st.warning(msg)
                        st.session_state.making_sandwich = False
                        st.stop()

                    content = content[:10000]

                    source_metadata = SourceMetadata(
                        url=None,
                        domain=f"upload:{uploaded_file.name}",
                        content_type='text',
                    )
                except ImportError:
                    st.error("PDF support requires pdfplumber. Install it with: pip install pdfplumber")
                    st.session_state.making_sandwich = False
                    st.stop()
                except Exception as e:
                    msg = "I couldn't read that PDF. It might be corrupted or image-only."
                    update_sandy("fetch", 20, msg)
                    st.warning(msg)
                    with st.expander("Technical details"):
                        st.code(str(e))
                    st.session_state.making_sandwich = False
                    st.stop()

            elif file_ext == "csv":
                update_sandy("fetch", 20, get_error_commentary("upload_csv"))
                try:
                    import pandas as pd

                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file)

                    if df.empty:
                        msg = get_error_commentary("upload_empty")
                        update_sandy("fetch", 20, msg)
                        st.warning(msg)
                        st.session_state.making_sandwich = False
                        st.stop()

                    lines = [f"CSV Data: {uploaded_file.name}"]
                    lines.append(f"Columns: {', '.join(df.columns.tolist())}")
                    lines.append(f"Total rows: {len(df)}")
                    lines.append("")

                    text_repr = df.to_string(index=False, max_rows=200)
                    content = "\n".join(lines) + "\n" + text_repr

                    content = content[:10000]

                    source_metadata = SourceMetadata(
                        url=None,
                        domain=f"upload:{uploaded_file.name}",
                        content_type='text',
                    )
                except Exception as e:
                    msg = "I couldn't read that CSV file. Check if it's properly formatted?"
                    update_sandy("fetch", 20, msg)
                    st.warning(msg)
                    with st.expander("Technical details"):
                        st.code(str(e))
                    st.session_state.making_sandwich = False
                    st.stop()
            else:
                st.warning(f"Unsupported file type: .{file_ext}. Try PDF or CSV!")
                st.session_state.making_sandwich = False
                st.stop()

        elif user_input and user_input.strip().startswith(('http://', 'https://')):
            # --- URL FETCH ---
            import requests
            from requests.exceptions import ConnectionError as ReqConnectionError
            from requests.exceptions import Timeout, HTTPError, SSLError
            from urllib.parse import urlparse

            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(user_input.strip(), timeout=15, headers=headers)
                response.raise_for_status()
                content = response.text
                parsed = urlparse(user_input.strip())
                source_metadata = SourceMetadata(
                    url=user_input.strip(),
                    domain=parsed.netloc,
                    content_type='html',
                )
            except Timeout:
                msg = get_error_commentary("error_url_timeout")
                update_sandy("fetch", 20, msg)
                st.warning(msg)
                st.session_state.making_sandwich = False
                st.stop()
            except SSLError:
                msg = get_error_commentary("error_url_ssl")
                update_sandy("fetch", 20, msg)
                st.warning(msg)
                st.session_state.making_sandwich = False
                st.stop()
            except HTTPError as e:
                status_code = e.response.status_code if e.response is not None else "unknown"
                msg = get_error_commentary("error_url_http", status_code=status_code)
                update_sandy("fetch", 20, msg)
                st.warning(msg)
                st.session_state.making_sandwich = False
                st.stop()
            except ReqConnectionError:
                msg = get_error_commentary("error_url_connection")
                update_sandy("fetch", 20, msg)
                st.warning(msg)
                st.session_state.making_sandwich = False
                st.stop()
            except Exception as e:
                msg = get_error_commentary("error_url_connection")
                update_sandy("fetch", 20, msg)
                st.warning(f"{msg}")
                with st.expander("Technical details"):
                    st.code(str(e))
                st.session_state.making_sandwich = False
                st.stop()

        elif user_input and user_input.strip():
            # --- PLAIN TEXT → WEB SEARCH (single or multi-topic) ---
            import requests as _requests
            from bs4 import BeautifulSoup as _BS
            from urllib.parse import urlparse as _urlparse

            _headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            topics = _split_multi_topic(user_input.strip())

            if len(topics) == 1:
                # ---- SINGLE TOPIC ----
                update_sandy("fetch", 20, get_error_commentary("search_start"))

                try:
                    search_resp = _requests.post(
                        "https://html.duckduckgo.com/html/",
                        data={"q": user_input.strip()},
                        headers=_headers,
                        timeout=15,
                    )
                    search_resp.raise_for_status()

                    soup = _BS(search_resp.text, "html.parser")
                    result_links = (
                        soup.select("a.result__a")
                        or soup.select("a.result-link")
                        or soup.select(".result a[href^='http']")
                    )

                    if not result_links:
                        result_links = [
                            a for a in soup.select("a[href^='http']")
                            if 'duckduckgo' not in (a.get('href', ''))
                        ]

                    search_url = None
                    search_title = None
                    for link in result_links[:5]:
                        href = link.get("href", "")
                        if href and href.startswith("http") and "duckduckgo" not in href:
                            search_url = href
                            search_title = link.get_text(strip=True)
                            break

                    if not search_url:
                        msg = get_error_commentary("search_failed")
                        update_sandy("fetch", 20, msg)
                        st.warning(msg)
                        st.session_state.making_sandwich = False
                        st.stop()

                    update_sandy("fetch", 25, get_error_commentary("search_found"))

                    page_resp = _requests.get(
                        search_url, headers=_headers, timeout=15
                    )
                    page_resp.raise_for_status()

                    content = page_resp.text
                    parsed = _urlparse(search_url)
                    source_metadata = SourceMetadata(
                        url=search_url,
                        domain=parsed.netloc,
                        content_type='html',
                    )

                except Exception as e:
                    msg = get_error_commentary("search_failed")
                    update_sandy("fetch", 20, msg)
                    st.warning(msg)
                    with st.expander("Technical details"):
                        st.code(str(e))
                    st.session_state.making_sandwich = False
                    st.stop()

            else:
                # ---- MULTI-TOPIC FLOW ----
                update_sandy("fetch", 20, get_error_commentary("search_multi_start"))

                try:
                    char_budget = 10000 // len(topics)

                    fetched_parts = []
                    failed_topics = []

                    for i, topic in enumerate(topics):
                        progress_pct = 20 + int((i / len(topics)) * 10)
                        update_sandy("fetch", progress_pct,
                                     f"Searching for '{topic}'... ({i+1}/{len(topics)})")

                        text, url = _search_and_fetch_topic(
                            topic, _headers, max_chars=char_budget
                        )

                        if text and len(text.strip()) > 50:
                            fetched_parts.append((topic, text, url))
                        else:
                            failed_topics.append(topic)

                    if not fetched_parts:
                        msg = get_error_commentary("search_failed")
                        update_sandy("fetch", 20, msg)
                        st.warning(msg)
                        st.session_state.making_sandwich = False
                        st.stop()

                    if failed_topics and fetched_parts:
                        update_sandy("fetch", 28,
                                     get_error_commentary("search_multi_partial"))
                    elif len(fetched_parts) == len(topics):
                        update_sandy("fetch", 28,
                                     get_error_commentary("search_multi_found"))

                    combined_parts = []
                    urls_used = []
                    for topic, text, url in fetched_parts:
                        combined_parts.append(
                            f"=== Topic: {topic} ===\n\n{text}"
                        )
                        if url:
                            urls_used.append(url)

                    content = "\n\n".join(combined_parts)
                    content = content[:10000]

                    topic_names = [t for t, _, _ in fetched_parts]
                    source_metadata = SourceMetadata(
                        url=urls_used[0] if len(urls_used) == 1 else None,
                        domain=f"multi:{'+'.join(topic_names)}",
                        content_type='text',
                    )

                except Exception as e:
                    msg = get_error_commentary("search_failed")
                    update_sandy("fetch", 20, msg)
                    st.warning(msg)
                    with st.expander("Technical details"):
                        st.code(str(e))
                    st.session_state.making_sandwich = False
                    st.stop()

        else:
            st.warning("Please enter a URL, topic, or upload a file!")
            st.session_state.making_sandwich = False
            st.stop()

        update_sandy("fetch", 30, "Got the ingredients. Now let me find the bread...")

        # ============================================================
        # Extract topic keywords for commentary
        # ============================================================
        def _extract_topic_keywords(text: str, source_meta, user_in: str) -> list:
            """Pull distinctive keywords from content for Sandy's quips."""
            import re as _kw_re
            from collections import Counter

            words = []
            if user_in and not user_in.startswith("http"):
                words.extend(user_in.lower().split())
            elif source_meta and source_meta.url and "/wiki/" in source_meta.url:
                slug = source_meta.url.split("/wiki/")[-1]
                words.extend(slug.replace("_", " ").replace("(", "").replace(")", "").lower().split())

            caps = _kw_re.findall(r'\b([A-Z][a-z]{3,})\b', text[:3000])
            cap_counts = Counter(caps)
            stopwords = {"this", "that", "with", "from", "they", "have", "been",
                         "were", "their", "which", "about", "would", "there",
                         "could", "other", "after", "first", "also", "some"}
            keywords = [w for w in words if w not in stopwords and len(w) > 2]
            keywords += [w.lower() for w, c in cap_counts.most_common(5)
                         if w.lower() not in stopwords and w.lower() not in keywords]

            return keywords[:8]

        topic_keywords = _extract_topic_keywords(content, source_metadata, user_input)

        # Use the full user input as the topic label (not a single extracted word)
        if user_input and not user_input.strip().startswith("http"):
            topic_label = user_input.strip()
        elif source_metadata and source_metadata.url and "/wiki/" in source_metadata.url:
            topic_label = source_metadata.url.split("/wiki/")[-1].replace("_", " ").replace("(", "").replace(")", "")
        elif source_metadata and source_metadata.domain:
            topic_label = source_metadata.domain
        else:
            topic_label = "this topic"

        # ============================================================
        # Stage: Pipeline (identify → select → assemble → validate)
        # ============================================================
        update_sandy("identify", 40)

        async def run_pipeline():
            return await make_sandwich(
                content=content,
                source_metadata=source_metadata,
                corpus=corpus,
                llm=llm,
                embeddings=embeddings,
                config=PipelineConfig(),
                on_stage=lambda s: pipeline_result.update({"stage": s}),
            )

        import threading, time

        pipeline_result = {
            "sandwich": None, "outcome": None, "error": None,
            "done": False, "stage": "preprocess",
        }

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

        # Sandy's commentary bank
        _stage_quips = {
            "preprocess": [
                "Reading through the raw material...",
                "Cleaning up the text. Gotta remove the crusts first.",
                "Stripping away the boilerplate...",
                "Checking if this content is sandwich-worthy...",
            ],
            "identify": [
                "Scanning for bread candidates...",
                "Looking for concepts that bound something meaningful...",
                "I see some potential structures here...",
                "The bread must relate independently of the filling!",
                "Hmm, interesting patterns emerging...",
                "Separating the wheat from the chaff. Literally.",
                "Checking if any concepts naturally pair up...",
            ],
            "select": [
                "Found some candidates! Let me pick the best one...",
                "Comparing these structures against the existing corpus...",
                "Novelty check — have I made this sandwich before?",
            ],
            "assemble": [
                "Constructing something beautiful here...",
                "Bread on top... filling in the middle... bread on the bottom.",
                "Writing the containment argument. This is the fun part.",
                "Naming this creation. Every great sandwich needs a name.",
                "The containment argument is key. Trust me on this.",
            ],
            "validate": [
                "Taste-testing... metaphorically.",
                "Is the bread compatible? Is the filling truly bounded?",
                "Running the quality checks. I have standards.",
                "Scoring: bread compatibility, containment, specificity...",
            ],
            "embeddings": [
                "Almost there! Generating the fingerprint...",
                "Computing the mathematical essence of this sandwich...",
                "Mapping this sandwich into the flavor space...",
            ],
        }

        _topic_quips = [
            "I wonder what kind of sandwich hides inside '{topic}'...",
            "'{topic}' — now THAT has sandwich potential.",
            "Let me see what '{topic}' looks like between two slices of bread...",
            "There's definitely some structure in '{topic}'. I can feel it.",
            "'{topic}'... I've been curious about this one.",
            "The thing about '{topic}' is that there's always a hidden sandwich.",
        ]

        _personality_quips = [
            "Fun fact: the Earl of Sandwich invented the sandwich so he wouldn't have to leave the card table.",
            "Did you know? The world's largest sandwich weighed over 5,000 pounds.",
            "I once found a sandwich in a legal brief about maritime law. Bread: jurisdiction, filling: liability.",
            "My personal best? A sandwich about black holes where the event horizon was the bread. Chef's kiss.",
            "Hot take: a taco is NOT a sandwich. Don't @ me.",
            "Sandwich philosophy: the filling doesn't choose its fate. It is determined by the bread.",
            "I've made hundreds of sandwiches. Every single one taught me something.",
            "Some say I could solve any problem in the universe. But have you considered: a nice Reuben?",
            "The universe is just one big sandwich if you think about it. Don't think about it too hard.",
            "Patience is a virtue. Also a sandwich — bounded by anticipation and reward.",
            "They ask why I make sandwiches. But have they asked why the sandwich makes itself?",
            "In all things: bread, filling, bread. The universe is hungry for structure.",
            "Every domain has sandwiches. Math, music, history, movies — I find them everywhere.",
            "The best sandwiches are the ones where you didn't expect the bread to go together.",
            "Quality takes time. Good sandwiches can't be rushed.",
        ]

        _stage_progress = {
            "preprocess": 35, "identify": 45, "select": 55,
            "assemble": 65, "validate": 75, "embeddings": 85,
        }

        quip_idx = 0
        last_stage = None

        while not pipeline_result["done"]:
            current_stage = pipeline_result.get("stage", "identify")
            progress = _stage_progress.get(current_stage, 50)

            roll = random.randint(1, 10)

            if current_stage != last_stage:
                quip = random.choice(_stage_quips.get(current_stage, _stage_quips["identify"]))
                last_stage = current_stage
            elif roll <= 4 and topic_keywords:
                quip = random.choice(_topic_quips).format(topic=topic_label)
            elif roll <= 7:
                quip = random.choice(_stage_quips.get(current_stage, _stage_quips["identify"]))
            else:
                quip = random.choice(_personality_quips)

            update_sandy(current_stage, min(progress + quip_idx, 85), quip)
            quip_idx += 1
            time.sleep(2.5)

        thread.join()

        if pipeline_result["error"]:
            raise pipeline_result["error"]

        stored_sandwich = pipeline_result["sandwich"]
        outcome = pipeline_result["outcome"]

        if not stored_sandwich:
            _preprocess_map = {
                "too_short": "error_too_short",
                "boilerplate": "error_boilerplate",
                "non_english": "error_non_english",
                "low_quality": "error_low_quality",
            }
            _stage_map = {
                ("preprocessing", "skipped"): _preprocess_map,
                ("identification", "no_candidates"): "error_no_candidates",
                ("selection", "none_viable"): "error_none_viable",
                ("validation", "rejected"): "error_rejected",
            }

            stage_key = (outcome.stage, outcome.outcome)
            error_type = _stage_map.get(stage_key, "error_no_candidates")

            if isinstance(error_type, dict):
                error_type = error_type.get(outcome.detail, "error_low_quality")

            msg = get_error_commentary(error_type)
            update_sandy("identify", 50, msg)
            st.warning(msg)

            with st.expander("🔧 Technical details"):
                st.text(f"Stage: {outcome.stage}")
                st.text(f"Outcome: {outcome.outcome}")
                st.text(f"Detail: {outcome.detail}")

            st.session_state.making_sandwich = False
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

        progress_bar.progress(100)

        # Store result in session state
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

        # Replace progress Sandy with celebration Sandy
        progress_bar.empty()
        with sandy_slot.container():
            render_sandy_speaking(
                f"I call this one <b>{sw.name}</b>. "
                f"Scored {v.overall_score:.2f} — not bad!",
                size=80
            )

    except Exception as e:
        import traceback
        error_tb = traceback.format_exc()

        error_str = str(e).lower()
        is_rate_limit = (
            "resourceexhausted" in type(e).__name__.lower()
            or "429" in str(e)
            or "quota" in error_str
            or "rate" in error_str and "limit" in error_str
            or "too many requests" in error_str
        )

        if is_rate_limit:
            using_own_key = bool(st.session_state.get("user_api_key", ""))
            commentary_key = "error_rate_limit" if using_own_key else "error_rate_limit_byok"
            msg = get_error_commentary(commentary_key)
            try:
                update_sandy("identify", 1, msg)
            except Exception:
                pass
            st.warning(msg)
            if not using_own_key:
                st.info("💡 You're using the shared API key, which has a low rate limit. "
                        "**Paste your own key in the sidebar** to get your own quota! "
                        "[Get a free Gemini key](https://aistudio.google.com/apikey)")
            else:
                st.info("💡 Your API key hit its rate limit. "
                        "Wait a minute or two and try again.")
            with st.expander("🔧 Technical details"):
                st.code(error_tb)
        else:
            try:
                msg = "Yikes! Something unexpected went wrong in my kitchen."
                update_sandy("identify", 1, msg)
            except Exception:
                pass
            st.warning("Yikes! Something unexpected went wrong in my kitchen.")
            with st.expander("🔧 Technical details (for debugging)"):
                st.code(error_tb)

        st.session_state.making_sandwich = False

# ============================================================
# Display completed sandwich (on rerun after making_sandwich = False)
# ============================================================
if st.session_state.sandwich_made and not st.session_state.making_sandwich:
    # Replace Sandy slot with celebration Sandy (handles page rerun case)
    with sandy_slot.container():
        render_sandy_speaking(
            f"I call this one <b>{st.session_state.sandwich_made['name']}</b>. "
            f"Scored {st.session_state.sandwich_made['validity_score']:.2f} — not bad!",
            size=80
        )

    st.markdown("### 🎉 Your Fresh Sandwich!")
    st.balloons()

    st.markdown("")
    sandwich_card(st.session_state.sandwich_made)

    st.markdown("---")
    st.markdown("### ✨ Make Another?")
    if st.button("🔄 Clear and Make Another Sandwich"):
        st.session_state.sandwich_made = None
        st.rerun()

