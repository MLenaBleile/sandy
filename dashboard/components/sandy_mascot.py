"""Sandy mascot SVG component.

Renders Sandy as a cute lavender cube with olive-green eyes and a sprout.
Supports speech bubbles and CSS animation.
"""

import streamlit as st


# Sandy SVG - lavender cube with eyes and sprout
# Isometric cube: corner faces the viewer, top face is a flat diamond.
# Draw order: left face → right face → top face → sprout → eyes (both on right face)
SANDY_SVG = """
<svg viewBox="0 -10 200 300" xmlns="http://www.w3.org/2000/svg" style="max-width:{size}px;">
  <!-- Cube - left face (darker) -->
  <polygon points="100,165 25,130 25,230 100,265" fill="#9a9bc7" stroke="#8384b3" stroke-width="1.5"/>

  <!-- Cube - right face (lighter) -->
  <polygon points="100,165 175,130 175,230 100,265" fill="#b8b9dd" stroke="#8384b3" stroke-width="1.5"/>

  <!-- Cube - top face (flat diamond) -->
  <polygon points="25,130 100,95 175,130 100,165" fill="#c8c9e8" stroke="#8384b3" stroke-width="1.5"/>

  <!-- Sprout -->
  <g transform="translate(100, 130)">
    <line x1="0" y1="0" x2="0" y2="-30" stroke="#3d6b2e" stroke-width="3" stroke-linecap="round"/>
    <path d="M0 -25 Q-8 -38 -14 -45 Q-20 -52 -12 -56 Q-5 -47 0 -32" fill="#5a9e3a" stroke="#3d6b2e" stroke-width="1.5"/>
    <path d="M0 -25 Q8 -40 16 -47 Q24 -54 19 -59 Q11 -50 5 -35" fill="#6bb84a" stroke="#3d6b2e" stroke-width="1.5"/>
    <path d="M0 -25 Q-6 -35 -12 -39 Q-18 -43 -14 -49" fill="none" stroke="#d4757a" stroke-width="2" stroke-linecap="round" opacity="0.8"/>
  </g>

  <!-- Eyes (both on the right face) -->
  <g>
    <ellipse cx="120" cy="190" rx="12" ry="13" fill="#5a5e4a" stroke="#3a3e2a" stroke-width="1"/>
    <ellipse cx="120" cy="190" rx="9" ry="10" fill="#6b7058"/>
    <circle cx="117" cy="193" r="3" fill="#8a8f75" opacity="0.6"/>
    <circle cx="120" cy="190" r="4" fill="#2a2e1a"/>
  </g>
  <g>
    <ellipse cx="150" cy="176" rx="12" ry="13" fill="#5a5e4a" stroke="#3a3e2a" stroke-width="1"/>
    <ellipse cx="150" cy="176" rx="9" ry="10" fill="#6b7058"/>
    <circle cx="147" cy="173" r="3" fill="#8a8f75" opacity="0.6"/>
    <circle cx="150" cy="176" r="4" fill="#2a2e1a"/>
  </g>
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
    0%, 100% {{ transform: translate(100px, 130px) rotate(0deg); }}
    25% {{ transform: translate(100px, 130px) rotate(3deg); }}
    75% {{ transform: translate(100px, 130px) rotate(-3deg); }}
  }}
  .sandy-container {{
    animation: sandy-bob 3s ease-in-out infinite;
    display: inline-block;
    flex-shrink: 0;
  }}
  .sandy-eye {{
    animation: sandy-blink 4s ease-in-out infinite;
  }}
  .sandy-sprout {{
    animation: sprout-sway 2.5s ease-in-out infinite;
    transform-origin: 0px 0px;
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
    min-height: 160px;
  }}
</style>
<div class="sandy-thinking">
  <div class="sandy-container">
    <svg viewBox="0 -10 200 300" xmlns="http://www.w3.org/2000/svg" width="{size}">
      <!-- Cube left face -->
      <polygon points="100,165 25,130 25,230 100,265" fill="#9a9bc7" stroke="#8384b3" stroke-width="1.5"/>
      <!-- Cube right face -->
      <polygon points="100,165 175,130 175,230 100,265" fill="#b8b9dd" stroke="#8384b3" stroke-width="1.5"/>
      <!-- Cube top face -->
      <polygon points="25,130 100,95 175,130 100,165" fill="#c8c9e8" stroke="#8384b3" stroke-width="1.5"/>
      <!-- Sprout -->
      <g class="sandy-sprout" transform="translate(100, 130)">
        <line x1="0" y1="0" x2="0" y2="-30" stroke="#3d6b2e" stroke-width="3" stroke-linecap="round"/>
        <path d="M0 -25 Q-8 -38 -14 -45 Q-20 -52 -12 -56 Q-5 -47 0 -32" fill="#5a9e3a" stroke="#3d6b2e" stroke-width="1.5"/>
        <path d="M0 -25 Q8 -40 16 -47 Q24 -54 19 -59 Q11 -50 5 -35" fill="#6bb84a" stroke="#3d6b2e" stroke-width="1.5"/>
        <path d="M0 -25 Q-6 -35 -12 -39 Q-18 -43 -14 -49" fill="none" stroke="#d4757a" stroke-width="2" stroke-linecap="round" opacity="0.8"/>
      </g>
      <!-- Eyes (both on right face) -->
      <g class="sandy-eye" style="transform-origin: 120px 190px;">
        <ellipse cx="120" cy="190" rx="12" ry="13" fill="#5a5e4a" stroke="#3a3e2a" stroke-width="1"/>
        <ellipse cx="120" cy="190" rx="9" ry="10" fill="#6b7058"/>
        <circle cx="117" cy="193" r="3" fill="#8a8f75" opacity="0.6"/>
        <circle cx="120" cy="190" r="4" fill="#2a2e1a"/>
      </g>
      <g class="sandy-eye" style="transform-origin: 150px 176px;">
        <ellipse cx="150" cy="176" rx="12" ry="13" fill="#5a5e4a" stroke="#3a3e2a" stroke-width="1"/>
        <ellipse cx="150" cy="176" rx="9" ry="10" fill="#6b7058"/>
        <circle cx="147" cy="173" r="3" fill="#8a8f75" opacity="0.6"/>
        <circle cx="150" cy="176" r="4" fill="#2a2e1a"/>
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


# Sandy SVG only (animated, no speech bubble) — for use with separate bubble container
SANDY_SVG_ANIMATED_ONLY = """
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
    0%, 100% {{ transform: translate(100px, 130px) rotate(0deg); }}
    25% {{ transform: translate(100px, 130px) rotate(3deg); }}
    75% {{ transform: translate(100px, 130px) rotate(-3deg); }}
  }}
  .sandy-container {{
    animation: sandy-bob 3s ease-in-out infinite;
    display: inline-block;
  }}
  .sandy-eye {{
    animation: sandy-blink 4s ease-in-out infinite;
  }}
  .sandy-sprout {{
    animation: sprout-sway 2.5s ease-in-out infinite;
    transform-origin: 0px 0px;
  }}
</style>
<div class="sandy-container">
  <svg viewBox="0 -10 200 300" xmlns="http://www.w3.org/2000/svg" width="{size}">
    <polygon points="100,165 25,130 25,230 100,265" fill="#9a9bc7" stroke="#8384b3" stroke-width="1.5"/>
    <polygon points="100,165 175,130 175,230 100,265" fill="#b8b9dd" stroke="#8384b3" stroke-width="1.5"/>
    <polygon points="25,130 100,95 175,130 100,165" fill="#c8c9e8" stroke="#8384b3" stroke-width="1.5"/>
    <g class="sandy-sprout" transform="translate(100, 130)">
      <line x1="0" y1="0" x2="0" y2="-30" stroke="#3d6b2e" stroke-width="3" stroke-linecap="round"/>
      <path d="M0 -25 Q-8 -38 -14 -45 Q-20 -52 -12 -56 Q-5 -47 0 -32" fill="#5a9e3a" stroke="#3d6b2e" stroke-width="1.5"/>
      <path d="M0 -25 Q8 -40 16 -47 Q24 -54 19 -59 Q11 -50 5 -35" fill="#6bb84a" stroke="#3d6b2e" stroke-width="1.5"/>
      <path d="M0 -25 Q-6 -35 -12 -39 Q-18 -43 -14 -49" fill="none" stroke="#d4757a" stroke-width="2" stroke-linecap="round" opacity="0.8"/>
    </g>
    <g class="sandy-eye" style="transform-origin: 120px 190px;">
      <ellipse cx="120" cy="190" rx="12" ry="13" fill="#5a5e4a" stroke="#3a3e2a" stroke-width="1"/>
      <ellipse cx="120" cy="190" rx="9" ry="10" fill="#6b7058"/>
      <circle cx="117" cy="193" r="3" fill="#8a8f75" opacity="0.6"/>
      <circle cx="120" cy="190" r="4" fill="#2a2e1a"/>
    </g>
    <g class="sandy-eye" style="transform-origin: 150px 176px;">
      <ellipse cx="150" cy="176" rx="12" ry="13" fill="#5a5e4a" stroke="#3a3e2a" stroke-width="1"/>
      <ellipse cx="150" cy="176" rx="9" ry="10" fill="#6b7058"/>
      <circle cx="147" cy="173" r="3" fill="#8a8f75" opacity="0.6"/>
      <circle cx="150" cy="176" r="4" fill="#2a2e1a"/>
    </g>
  </svg>
</div>
"""

# Speech bubble only — for updating independently from Sandy
SPEECH_BUBBLE_HTML = """
<style>
  .speech-bubble-standalone {{
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
    margin-left: 1rem;
  }}
</style>
<div class="speech-bubble-standalone">{message}</div>
"""


def render_sandy_animated(size: int = 100) -> None:
    """Render just the animated Sandy SVG (no speech bubble).

    Use with render_speech_bubble() in separate st.empty() containers
    so Sandy stays in place while the bubble updates.
    """
    st.markdown(
        SANDY_SVG_ANIMATED_ONLY.format(size=size),
        unsafe_allow_html=True,
    )


def render_speech_bubble(message: str) -> None:
    """Render just the speech bubble (no Sandy).

    Use with render_sandy_animated() in separate st.empty() containers.
    """
    st.markdown(
        SPEECH_BUBBLE_HTML.format(message=message),
        unsafe_allow_html=True,
    )


# Sandy's commentary lines for each pipeline stage
SANDY_COMMENTARY = {
    "init": [
        "Let me take a look...",
        "Warming up the pattern detector.",
        "Alright, let's see what's in here.",
        "Cracking my knuckles. Well, if I had knuckles.",
    ],
    "fetch": [
        "Ooh, let me take a look at this...",
        "Pulling in the content...",
        "Reading, reading... I love reading.",
        "Hmm, there's a lot to chew on here.",
    ],
    "identify": [
        "I see some potential bread candidates here...",
        "Looking for structure...",
        "Is there a filling in here? Let me look closer.",
        "Separating the wheat from the chaff. Literally.",
        "The bread must relate independently of the filling!",
    ],
    "assemble": [
        "Bread on top... filling in the middle... bread on the bottom. Classic.",
        "I think I see something here.",
        "If this is real, it needs a containment argument.",
        "The containment argument is key. Trust me on this.",
    ],
    "validate": [
        "Now the real question — is this actually a sandwich?",
        "Checking bread compatibility... containment... specificity...",
        "Let me score it. I have standards.",
        "Not everything that looks like a sandwich is one.",
    ],
    "embed": [
        "Mapping this into the sandwich space...",
        "Finding where this fits in the corpus.",
        "Almost done! Just doing some math.",
    ],
    "save": [
        "Saving to the database! Another one for the collection.",
        "Filing this one away.",
        "Done! Adding it to the corpus.",
    ],
    # --- Error commentary (used by get_error_commentary) ---
    "error_too_short": [
        "Not enough content here for me to work with. Try something more substantial.",
        "That's barely a paragraph. I need more material to look through.",
        "Too short. I can't tell if there's a sandwich in something this brief.",
    ],
    "error_boilerplate": [
        "It's all cookie banners and subscribe buttons. No real content to search through.",
        "After stripping the web junk, there's nothing left. Try a different source.",
        "The page was 99% ads. I need actual content to look for sandwiches in.",
    ],
    "error_non_english": [
        "Interesting language! But I can only look for sandwiches in English for now.",
        "That's not in English — I can only work with English content right now.",
        "My pattern detection only works in English, unfortunately.",
    ],
    "error_low_quality": [
        "I looked through this, but the content doesn't have enough structure to work with.",
        "Not enough substance here for me to find anything. Try something richer.",
        "The content is too thin. There might be a sandwich in a better source on this topic.",
    ],
    "error_no_candidates": [
        "No sandwich here. I looked, but there's no bread — just a lot of filling with nothing to bound it.",
        "This one's more of a soup than a sandwich. Interesting content, but no bounding structure.",
        "I couldn't find any bread in there. Not everything has a sandwich in it — and that's okay.",
        "No sandwich-shaped structures hiding in this one. Try a different angle on the topic?",
    ],
    "error_none_viable": [
        "I saw some possibilities, but nothing that holds together. No real sandwich here.",
        "Close, but not quite. The structures I found didn't have enough integrity to count.",
        "I had some ideas, but they'd fall apart under scrutiny. This one's a no.",
    ],
    "error_rejected": [
        "I found something, but it didn't pass my quality bar. Not a real sandwich.",
        "Almost! But my validator said no. The structure wasn't strong enough.",
        "It looked like a sandwich at first, but on closer inspection — nah.",
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
    "error_rate_limit_byok": [
        "The shared kitchen is too crowded! Bring your own key — there's a spot in the sidebar. 🔑",
        "Too many cooks in this kitchen! Paste your own API key in the sidebar to get your own lane.",
        "Rate limited on the communal key. Check the sidebar — you can add your own for free!",
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
