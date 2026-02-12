"""Sandy mascot SVG component.

Renders Sandy as a cute lavender cube with olive-green eyes and a sprout.
Supports speech bubbles and CSS animation.
"""

import streamlit as st


# Sandy SVG - lavender cube with eyes and sprout
# Draw order: bottom face → left face → right face → top face → sprout → eyes
# Sprout is drawn AFTER top face so the stem overlaps onto the surface
SANDY_SVG = """
<svg viewBox="0 0 200 270" xmlns="http://www.w3.org/2000/svg" style="max-width:{size}px;">
  <!-- Cube - bottom face (darkest) -->
  <polygon points="20,140 90,205 175,230 105,265" fill="#8384b3" stroke="#8384b3" stroke-width="1"/>

  <!-- Cube - left face (darker) -->
  <polygon points="20,140 90,105 90,205 20,240" fill="#9a9bc7" stroke="#8384b3" stroke-width="1.5"/>

  <!-- Cube - right face (lighter) -->
  <polygon points="90,105 175,130 175,230 90,205" fill="#b8b9dd" stroke="#8384b3" stroke-width="1.5"/>

  <!-- Cube - top face -->
  <polygon points="20,140 90,105 175,130 105,165" fill="#c8c9e8" stroke="#8384b3" stroke-width="1.5"/>

  <!-- Sprout (drawn after top face so stem overlaps onto surface) -->
  <line x1="100" y1="118" x2="100" y2="75" stroke="#4a6e3a" stroke-width="2.5" stroke-linecap="round"/>
  <path d="M100 75 Q97 58 93 48 Q87 38 95 30 Q100 36 100 48" fill="#6b8e5a" stroke="#4a6e3a" stroke-width="1"/>
  <path d="M100 75 Q103 56 110 46 Q117 36 113 26 Q105 32 103 46" fill="#7da668" stroke="#4a6e3a" stroke-width="1"/>
  <path d="M100 75 Q95 62 88 57 Q83 52 87 45" fill="#c47a7a" stroke="#a05a5a" stroke-width="0.8" opacity="0.7"/>

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
  }}
  .speech-bubble::after {{
    content: '';
    position: absolute;
    left: -12px;
    top: 50%;
    transform: translateY(-50%);
    border-width: 10px 12px 10px 0;
    border-style: solid;
    border-color: transparent #ffb6c1 transparent transparent;
  }}
  .speech-bubble::before {{
    content: '';
    position: absolute;
    left: -9px;
    top: 50%;
    transform: translateY(-50%);
    border-width: 8px 10px 8px 0;
    border-style: solid;
    border-color: transparent #fffbf0 transparent transparent;
    z-index: 1;
  }}
  .sandy-thinking {{
    display: flex;
    align-items: center;
    gap: 16px;
    justify-content: center;
    padding: 1rem 0;
  }}
</style>
<div class="sandy-thinking">
  <div class="sandy-container">
    <svg viewBox="0 0 200 270" xmlns="http://www.w3.org/2000/svg" width="{size}">
      <!-- Cube bottom face -->
      <polygon points="20,140 90,205 175,230 105,265" fill="#8384b3" stroke="#8384b3" stroke-width="1"/>
      <!-- Cube left face -->
      <polygon points="20,140 90,105 90,205 20,240" fill="#9a9bc7" stroke="#8384b3" stroke-width="1.5"/>
      <!-- Cube right face -->
      <polygon points="90,105 175,130 175,230 90,205" fill="#b8b9dd" stroke="#8384b3" stroke-width="1.5"/>
      <!-- Cube top face -->
      <polygon points="20,140 90,105 175,130 105,165" fill="#c8c9e8" stroke="#8384b3" stroke-width="1.5"/>
      <!-- Sprout (drawn after top face, stem overlaps onto surface) -->
      <g class="sandy-sprout" transform="translate(100, 118)">
        <line x1="0" y1="0" x2="0" y2="-43" stroke="#4a6e3a" stroke-width="2.5" stroke-linecap="round"/>
        <path d="M0 -43 Q-3 -60 -7 -70 Q-13 -80 -5 -88 Q0 -82 0 -70" fill="#6b8e5a" stroke="#4a6e3a" stroke-width="1"/>
        <path d="M0 -43 Q3 -62 10 -72 Q17 -82 13 -92 Q5 -86 3 -72" fill="#7da668" stroke="#4a6e3a" stroke-width="1"/>
        <path d="M0 -43 Q-5 -56 -12 -61 Q-17 -66 -13 -73" fill="#c47a7a" stroke="#a05a5a" stroke-width="0.8" opacity="0.7"/>
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
