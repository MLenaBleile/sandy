"""Sandy mascot SVG component.

Renders Sandy as a cute lavender cube with olive-green eyes and a sprout.
Supports speech bubbles and CSS animation.
"""

import streamlit as st


# Sandy SVG - lavender cube with eyes and sprout
SANDY_SVG = """
<svg viewBox="0 0 200 250" xmlns="http://www.w3.org/2000/svg" style="max-width:{size}px;">
  <!-- Sprout (stem connects to cube top) -->
  <g transform="translate(85, 30)">
    <line x1="15" y1="78" x2="15" y2="55" stroke="#4a6e3a" stroke-width="2.5" stroke-linecap="round"/>
    <path d="M15 55 Q12 38 8 28 Q2 18 10 10 Q15 16 15 28" fill="#6b8e5a" stroke="#4a6e3a" stroke-width="1"/>
    <path d="M15 55 Q18 36 25 26 Q32 16 28 6 Q20 12 18 26" fill="#7da668" stroke="#4a6e3a" stroke-width="1"/>
    <path d="M15 55 Q10 42 3 37 Q-2 32 2 25" fill="#c47a7a" stroke="#a05a5a" stroke-width="0.8" opacity="0.7"/>
  </g>

  <!-- Cube - left face (darker) -->
  <polygon points="20,140 90,105 90,205 20,240" fill="#9a9bc7" stroke="#8384b3" stroke-width="1.5"/>

  <!-- Cube - right face (lighter) -->
  <polygon points="90,105 175,130 175,230 90,205" fill="#b8b9dd" stroke="#8384b3" stroke-width="1.5"/>

  <!-- Cube - bottom face (darkest, visible edge) -->
  <polygon points="20,240 90,205 175,230 105,265" fill="#8384b3" stroke="#8384b3" stroke-width="1"/>

  <!-- Cube - top face -->
  <polygon points="20,140 90,105 175,130 105,165" fill="#c8c9e8" stroke="#8384b3" stroke-width="1.5"/>

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
    <svg viewBox="0 0 200 250" xmlns="http://www.w3.org/2000/svg" width="{size}">
      <!-- Sprout (stem connects to cube top) -->
      <g class="sandy-sprout" transform="translate(85, 30)">
        <line x1="15" y1="78" x2="15" y2="55" stroke="#4a6e3a" stroke-width="2.5" stroke-linecap="round"/>
        <path d="M15 55 Q12 38 8 28 Q2 18 10 10 Q15 16 15 28" fill="#6b8e5a" stroke="#4a6e3a" stroke-width="1"/>
        <path d="M15 55 Q18 36 25 26 Q32 16 28 6 Q20 12 18 26" fill="#7da668" stroke="#4a6e3a" stroke-width="1"/>
        <path d="M15 55 Q10 42 3 37 Q-2 32 2 25" fill="#c47a7a" stroke="#a05a5a" stroke-width="0.8" opacity="0.7"/>
      </g>
      <!-- Cube left face -->
      <polygon points="20,140 90,105 90,205 20,240" fill="#9a9bc7" stroke="#8384b3" stroke-width="1.5"/>
      <!-- Cube right face -->
      <polygon points="90,105 175,130 175,230 90,205" fill="#b8b9dd" stroke="#8384b3" stroke-width="1.5"/>
      <!-- Cube bottom face -->
      <polygon points="20,240 90,205 175,230 105,265" fill="#8384b3" stroke="#8384b3" stroke-width="1"/>
      <!-- Cube top face -->
      <polygon points="20,140 90,105 175,130 105,165" fill="#c8c9e8" stroke="#8384b3" stroke-width="1.5"/>
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
