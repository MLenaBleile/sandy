"""Sandy mascot SVG component.

Renders Sandy as a cute lavender cube with olive-green eyes and a sprout.
Supports speech bubbles and CSS animation.
"""

import streamlit as st


# Sandy SVG - lavender cube with eyes and sprout
# Draw order: left face → right face → bottom face → top face → sprout → eyes
# Sprout drawn AFTER top face so the stem overlaps onto the surface
SANDY_SVG = """
<svg viewBox="0 0 200 280" xmlns="http://www.w3.org/2000/svg" style="max-width:{size}px;">
  <!-- Cube - left face (darker) -->
  <polygon points="20,140 90,105 90,205 20,240" fill="#9a9bc7" stroke="#8384b3" stroke-width="1.5"/>

  <!-- Cube - right face (lighter) -->
  <polygon points="90,105 175,130 175,230 90,205" fill="#b8b9dd" stroke="#8384b3" stroke-width="1.5"/>

  <!-- Cube - bottom face (darkest, closing the base) -->
  <polygon points="20,240 90,205 175,230 105,265" fill="#8384b3" stroke="#7374a3" stroke-width="1"/>

  <!-- Cube - top face -->
  <polygon points="20,140 90,105 175,130 105,165" fill="#c8c9e8" stroke="#8384b3" stroke-width="1.5"/>

  <!-- Sprout stem (planted into top face surface, drawn on top of it) -->
  <line x1="100" y1="120" x2="100" y2="68" stroke="#4a6e3a" stroke-width="3" stroke-linecap="round"/>
  <!-- Left leaf -->
  <path d="M100 68 Q96 48 90 38 Q84 26 92 18 Q98 28 100 42" fill="#6b8e5a" stroke="#4a6e3a" stroke-width="1.2"/>
  <!-- Right leaf -->
  <path d="M100 68 Q104 46 112 36 Q120 24 116 14 Q108 22 106 40" fill="#7da668" stroke="#4a6e3a" stroke-width="1.2"/>
  <!-- Small accent leaf / bud -->
  <path d="M100 68 Q94 54 86 48 Q80 44 84 36" fill="none" stroke="#c47a7a" stroke-width="1.5" stroke-linecap="round" opacity="0.7"/>

  <!-- Left eye -->
  <ellipse cx="118" cy="160" rx="12" ry="13" fill="#5a5e4a" stroke="#3a3e2a" stroke-width="1"/>
  <ellipse cx="118" cy="160" rx="9" ry="10" fill="#6b7058"/>
  <circle cx="115" cy="157" r="3" fill="#8a8f75" opacity="0.6"/>
  <circle cx="118" cy="160" r="4" fill="#2a2e1a"/>

  <!-- Right eye -->
  <ellipse cx="148" cy="168" rx="12" ry="13" fill="#5a5e4a" stroke="#3a3e2a" stroke-width="1"/>
  <ellipse cx="148" cy="168" rx="9" ry="10" fill="#6b7058"/>
  <circle cx="145" cy="165" r="3" fill="#8a8f75" opacity="0.6"/>
  <circle cx="148" cy="168" r="4" fill="#2a2e1a"/>
</svg>
"""

# Animated version with gentle bobbing
SANDY_SVG_ANIMATED = """
<style>
  @keyframes sandy-bob {{
    0%, 100% {{ transform: translateY(0px); }}
    50% {{ transform: translateY(-6px); }}
  }}
  @keyframes sandy-blink {{
    0%, 90%, 100% {{ transform: scaleY(1); }}
    95% {{ transform: scaleY(0.1); }}
  }}
  @keyframes sprout-sway {{
    0%, 100% {{ transform: rotate(0deg); }}
    25% {{ transform: rotate(3deg); }}
    75% {{ transform: rotate(-3deg); }}
  }}
  .sandy-container {{
    animation: sandy-bob 3s ease-in-out infinite;
    display: inline-block;
  }}
  .sandy-eyes {{
    animation: sandy-blink 4s ease-in-out infinite;
    transform-origin: center;
  }}
  .sandy-sprout {{
    animation: sprout-sway 2.5s ease-in-out infinite;
    transform-origin: bottom center;
  }}
  .speech-bubble {{
    background: linear-gradient(135deg, #fffbf0 0%, #fff5f8 100%);
    border: 2px solid #ffb6c1;
    border-radius: 16px;
    padding: 14px 18px;
    font-size: 0.95rem;
    color: #555;
    font-style: italic;
    position: relative;
    box-shadow: 0 3px 10px rgba(255, 107, 157, 0.15);
    max-width: 400px;
    min-height: 40px;
    margin-top: 20px;
  }}
  .speech-bubble::after {{
    content: '';
    position: absolute;
    left: -12px;
    top: 24px;
    border-width: 10px 12px 10px 0;
    border-style: solid;
    border-color: transparent #ffb6c1 transparent transparent;
  }}
  .speech-bubble::before {{
    content: '';
    position: absolute;
    left: -9px;
    top: 26px;
    border-width: 8px 10px 8px 0;
    border-style: solid;
    border-color: transparent #fffbf0 transparent transparent;
    z-index: 1;
  }}
  .sandy-thinking {{
    display: flex;
    align-items: flex-start;
    gap: 16px;
    justify-content: center;
    padding: 1rem 0;
  }}
</style>
<div class="sandy-thinking">
  <div class="sandy-container">
    <svg viewBox="0 0 200 280" xmlns="http://www.w3.org/2000/svg" width="{size}">
      <!-- Cube left face -->
      <polygon points="20,140 90,105 90,205 20,240" fill="#9a9bc7" stroke="#8384b3" stroke-width="1.5"/>
      <!-- Cube right face -->
      <polygon points="90,105 175,130 175,230 90,205" fill="#b8b9dd" stroke="#8384b3" stroke-width="1.5"/>
      <!-- Cube bottom face -->
      <polygon points="20,240 90,205 175,230 105,265" fill="#8384b3" stroke="#7374a3" stroke-width="1"/>
      <!-- Cube top face -->
      <polygon points="20,140 90,105 175,130 105,165" fill="#c8c9e8" stroke="#8384b3" stroke-width="1.5"/>
      <!-- Sprout (drawn after top face, planted into surface) -->
      <g class="sandy-sprout" transform="translate(100, 120)">
        <line x1="0" y1="0" x2="0" y2="-52" stroke="#4a6e3a" stroke-width="3" stroke-linecap="round"/>
        <path d="M0 -52 Q-4 -72 -10 -82 Q-16 -94 -8 -102 Q-2 -92 0 -78" fill="#6b8e5a" stroke="#4a6e3a" stroke-width="1.2"/>
        <path d="M0 -52 Q4 -74 12 -84 Q20 -96 16 -106 Q8 -98 6 -80" fill="#7da668" stroke="#4a6e3a" stroke-width="1.2"/>
        <path d="M0 -52 Q-6 -66 -14 -72 Q-20 -76 -16 -84" fill="none" stroke="#c47a7a" stroke-width="1.5" stroke-linecap="round" opacity="0.7"/>
      </g>
      <!-- Eyes -->
      <g class="sandy-eyes">
        <ellipse cx="118" cy="160" rx="12" ry="13" fill="#5a5e4a" stroke="#3a3e2a" stroke-width="1"/>
        <ellipse cx="118" cy="160" rx="9" ry="10" fill="#6b7058"/>
        <circle cx="115" cy="157" r="3" fill="#8a8f75" opacity="0.6"/>
        <circle cx="118" cy="160" r="4" fill="#2a2e1a"/>
        <ellipse cx="148" cy="168" rx="12" ry="13" fill="#5a5e4a" stroke="#3a3e2a" stroke-width="1"/>
        <ellipse cx="148" cy="168" rx="9" ry="10" fill="#6b7058"/>
        <circle cx="145" cy="165" r="3" fill="#8a8f75" opacity="0.6"/>
        <circle cx="148" cy="168" r="4" fill="#2a2e1a"/>
      </g>
    </svg>
  </div>
  <div>
    <div class="speech-bubble">{message}</div>
  </div>
</div>
"""


def render_sandy(size: int = 120) -> None:
    """Render the static Sandy mascot.

    Args:
        size: Width in pixels.
    """
    st.markdown(SANDY_SVG.format(size=size), unsafe_allow_html=True)


def render_sandy_speaking(message: str, size: int = 100) -> None:
    """Render Sandy with an animated speech bubble.

    Args:
        message: Text to show in the speech bubble.
        size: Width of Sandy SVG in pixels.
    """
    st.markdown(
        SANDY_SVG_ANIMATED.format(message=message, size=size),
        unsafe_allow_html=True,
    )


# Sandy's commentary lines for each pipeline stage
SANDY_COMMENTARY = {
    "init": [
        "Warming up the toaster... figuratively speaking.",
        "Let me get my apron on...",
        "Time to make something delicious!",
        "Cracking my knuckles. Well, if I had knuckles.",
    ],
    "fetch": [
        "Ooh, let me take a look at this...",
        "Fetching ingredients from the internet pantry!",
        "Reading, reading... I love reading.",
        "Hmm, there's a lot to chew on here.",
    ],
    "identify": [
        "I see some potential bread candidates here...",
        "Looking for the perfect pairing...",
        "Is that a filling I spot? Let me look closer.",
        "Separating the wheat from the chaff. Literally.",
        "The bread must relate independently of the filling!",
    ],
    "assemble": [
        "Bread on top... filling in the middle... bread on the bottom. Classic.",
        "Constructing something beautiful here.",
        "Every great sandwich tells a story.",
        "The containment argument is key. Trust me on this.",
    ],
    "validate": [
        "Let me taste-test this... metaphorically.",
        "Checking bread compatibility... containment... specificity...",
        "Is this sandwich worthy? Let me score it.",
        "Quality control is my middle name. Well, not really.",
    ],
    "embed": [
        "Mapping this sandwich into the cosmic embedding space...",
        "Finding where this fits in the grand sandwich universe.",
        "Almost done! Just doing some math.",
    ],
    "save": [
        "Saving to the database! Another one for the collection.",
        "Filing this masterpiece away for posterity.",
        "Done! Fresh out of the oven. Well, the algorithm.",
    ],
    # --- Error commentary (used by get_error_commentary) ---
    "error_too_short": [
        "That's barely a crumb! I need more material to work with.",
        "Not enough to spread on a single slice. Try something with more content!",
        "I've seen longer fortune cookies. Need more substance for a proper sandwich!",
    ],
    "error_boilerplate": [
        "It's all cookie banners and subscribe buttons. No real content left!",
        "After peeling off the web junk, there was nothing underneath. Like an onion made entirely of skin.",
        "The page was 99% ads and 1% content. Even I can't make a sandwich out of thin air!",
    ],
    "error_non_english": [
        "Interesting language! But I only make sandwiches in English for now. Sorry!",
        "My bread only rises in English, unfortunately. Try an English-language source!",
        "That's not in English — my recipe book only covers one language right now!",
    ],
    "error_low_quality": [
        "The quality of this content is... let's just say my standards are higher.",
        "I tried, I really did. But this content doesn't have the right texture for a sandwich.",
        "Not every ingredient makes the cut. This one didn't pass my quality inspection!",
    ],
    "error_no_candidates": [
        "All filling, no structure. I looked everywhere but couldn't find any bread in there!",
        "It's like a soup — lots of stuff, but nothing to hold it together as a sandwich.",
        "I scoured the content but couldn't find any bounding concepts. No bread, no sandwich!",
        "The content is interesting, but there aren't any sandwich-shaped structures hiding in it.",
    ],
    "error_none_viable": [
        "I found some candidates, but none passed the taste test. Too bland!",
        "Close, but no sandwich. The candidates didn't have enough structural integrity.",
        "I had some ideas, but honestly? They'd fall apart. I have standards!",
    ],
    "error_rejected": [
        "I assembled one, but it didn't pass quality control. I'm a perfectionist.",
        "Almost had it! But my validator said 'nope.' Better luck with the next source!",
        "The sandwich was technically a sandwich, but it wasn't a *good* sandwich. I let it go.",
    ],
    "error_url_connection": [
        "Hmm, the door's locked on this one. Can't reach the server!",
        "The internet gremlins are blocking me. The site might be down!",
        "I knocked, but nobody answered. Try again in a moment?",
    ],
    "error_url_timeout": [
        "Still waiting... still waiting... nope, the page took too long to respond!",
        "That URL is slower than a snail on a sandwich. Timed out!",
        "I don't have all day — well, I do, but the connection timed out anyway!",
    ],
    "error_url_http": [
        "Got a {status_code} error from the server. Might be a broken link!",
        "The website said '{status_code}.' That's web-speak for 'go away.'",
        "This URL returned an error ({status_code}). Maybe double-check the address?",
    ],
    "error_url_ssl": [
        "The security certificate on this site looks fishy. Can't connect safely!",
        "SSL error — the secure connection couldn't be established.",
        "This site's security papers aren't in order. Can't safely fetch it!",
    ],
    "search_start": [
        "That doesn't look like a URL. Let me search for it!",
        "No URL? No problem! Sandy's got DuckDuckGo on speed dial.",
        "Let me look that up for you. One web search, coming right up!",
    ],
    "search_found": [
        "Found something! Let me grab the content from this page...",
        "Ooh, this search result looks promising. Fetching it now!",
        "The search turned up gold! Let me read through it...",
    ],
    "search_failed": [
        "My search came up empty. Try a different phrase or paste a direct URL!",
        "DuckDuckGo couldn't find anything useful. Maybe try rephrasing?",
        "No search results I could use. Try a URL instead!",
    ],
    "search_multi_start": [
        "Ooh, multiple topics! Let me search for each one separately.",
        "I see more than one topic here! Time for a multi-search.",
        "Two topics, one sandwich? Challenge accepted! Searching both...",
    ],
    "search_multi_found": [
        "Found content for both topics! Combining the ingredients...",
        "Got results for each topic. Let me mix these together...",
        "Both searches came back! Time to blend these worlds...",
    ],
    "search_multi_partial": [
        "I could only find content for one of the topics. Working with what I've got!",
        "One topic came up empty, but the other worked! Let me use that.",
        "Partial success — one search hit, one miss. Making do!",
    ],
    "upload_pdf": [
        "Ooh, a PDF! Let me read through this document...",
        "PDF detected! Time to extract some sandwich material.",
        "Reading your PDF now. I love a good document to chew on!",
    ],
    "upload_csv": [
        "A CSV file! Let me turn this data into something delicious...",
        "Spreadsheet time! Data can make surprisingly good sandwiches.",
        "CSV detected. Let me digest these rows and columns...",
    ],
    "upload_empty": [
        "This file seems empty. I can't make a sandwich from nothing!",
        "The file didn't have any content I could work with. Try another?",
        "Nothing to extract here. It's like opening a lunchbox and finding... air.",
    ],
    "error_rate_limit": [
        "I've been making too many sandwiches today! My kitchen needs a breather. Try again in a minute or two! 🫠",
        "Whoa, I hit my daily sandwich quota! The Gemini free tier only allows so many requests. Try again shortly!",
        "The API is telling me to slow down — too many requests! Give it a minute and try again. 🍞💤",
    ],
}


def get_commentary(stage: str, index: int = 0) -> str:
    """Get a Sandy commentary line for a pipeline stage.

    Args:
        stage: Pipeline stage key.
        index: Which line to pick (wraps around).

    Returns:
        A commentary string.
    """
    import random
    lines = SANDY_COMMENTARY.get(stage, SANDY_COMMENTARY["init"])
    return lines[index % len(lines)]


def get_error_commentary(error_type: str, **kwargs) -> str:
    """Get a random Sandy commentary line for an error scenario.

    Args:
        error_type: Key from SANDY_COMMENTARY (e.g., 'error_too_short').
        **kwargs: Format variables (e.g., status_code=404).

    Returns:
        A formatted commentary string.
    """
    import random
    lines = SANDY_COMMENTARY.get(
        error_type,
        SANDY_COMMENTARY.get("error_no_candidates", ["Something went wrong!"]),
    )
    line = random.choice(lines)
    try:
        return line.format(**kwargs)
    except (KeyError, IndexError):
        return line
