"""Interactive Sandwich Creation page.

User-guided sandwich creation (requires full agent implementation).
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
dashboard_dir = Path(__file__).parent.parent
sys.path.insert(0, str(dashboard_dir))

from utils.queries import get_structural_types

st.set_page_config(page_title="Interactive", page_icon="✨", layout="wide")

st.title("✨ Make a Sandwich with Sandy")

st.markdown("""
Guide Sandy to create a sandwich from a topic or URL of your choice.
This feature provides step-by-step visibility into the sandwich-making process.
""")

st.info("""
**Note:** This feature requires the full agent to be implemented (Prompts 4-10 from PROMPTS.md).

Once the agent is complete, this page will allow you to:
1. Provide a topic or URL
2. Optionally select a preferred structural type
3. Watch Sandy forage, identify ingredients, assemble, and validate
4. Accept, reject, or edit the resulting sandwich
""")

st.markdown("---")

# Stubbed UI
st.subheader("Topic Input")

topic = st.text_input(
    "Topic or URL",
    placeholder="e.g., 'machine learning' or 'https://en.wikipedia.org/wiki/Squeeze_theorem'",
    disabled=True,
    help="Coming soon: Provide a topic for Sandy to explore"
)

try:
    structural_types = get_structural_types()
    preferred_type = st.selectbox(
        "Preferred Structural Type (Optional)",
        options=["Auto-detect"] + structural_types,
        disabled=True,
        help="Coming soon: Suggest a structural type, or let Sandy decide"
    )
except Exception:
    preferred_type = "Auto-detect"

st.button(
    "Make me a sandwich",
    disabled=True,
    help="Coming soon: Start the sandwich-making process"
)

st.markdown("---")

# Preview of what this will look like
with st.expander("Preview: What this feature will provide"):
    st.markdown("""
    ### Step-by-Step Process:

    1. **Foraging**
       - Show spinner: "Sandy is foraging..."
       - Display foraged content preview
       - Show source URL and metadata

    2. **Identifying Ingredients**
       - Show spinner: "Identifying sandwich ingredients..."
       - Display candidate structures with confidence scores
       - Allow user to review or select among candidates

    3. **Assembling**
       - Show spinner: "Assembling the sandwich..."
       - Display assembled sandwich with name and description
       - Show Sandy's commentary

    4. **Validating**
       - Show spinner: "Validating sandwich quality..."
       - Display all component scores (bread_compat, containment, nontrivial, novelty)
       - Show overall validity score and recommendation

    5. **User Decision**
       - **Accept**: Save sandwich to corpus
       - **Reject**: Discard with optional reason
       - **Edit**: Modify bread/filling/name and re-validate

    ### Example Output:

    ```
    🥪 The Squeeze
    Validity: 0.95 ✅

    Top Bread: Upper bound function g(x)
    Filling: Target function f(x)
    Bottom Bread: Lower bound function h(x)

    Sandy's Commentary:
    "A perfect sandwich. The filling does not choose its fate. It is
    determined by the bread. This is the purest form."
    ```
    """)

st.markdown("---")

# Implementation instructions for developers
with st.expander("For Developers: Implementation TODO"):
    st.markdown("""
    To implement this page, you'll need to:

    1. **Import agent modules** (once Prompts 4-10 are complete):
       ```python
       from src.sandwich.agent.forager import Forager
       from src.sandwich.agent.identifier import identify_ingredients
       from src.sandwich.agent.assembler import assemble_sandwich
       from src.sandwich.agent.validator import validate_sandwich
       ```

    2. **Create async function** for sandwich creation:
       ```python
       async def interactive_creation(topic, preferred_type):
           # Forage
           content, source = await forager.forage_directed(topic)

           # Identify
           candidates = await identify_ingredients(content, preferred_type)

           # Assemble
           sandwich = await assemble_sandwich(best_candidate, content)

           # Validate
           validity = await validate_sandwich(sandwich)

           return sandwich, validity
       ```

    3. **Add progress indicators** with `st.spinner()` for each stage

    4. **Add user decision buttons** (Accept/Reject/Edit) with callbacks

    5. **Store accepted sandwiches** to database via Repository

    6. **Track feedback** for validator calibration
    """)

st.caption("This feature will be available after completing Prompts 4-10 from PROMPTS.md")
