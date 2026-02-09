"""Color palette for the Reuben dashboard.

Defines consistent color scheme across all dashboard components, including
structural type colors, validity score colors, and UI element colors.

Based on SPEC.md Section 14.5
"""

# Structural type colors (distinct, accessible)
COLORS = {
    # Structural types (10 types from SPEC.md Section 4.2)
    'bound': '#4A90E2',         # Blue
    'dialectic': '#E27D60',     # Coral
    'epistemic': '#85DCB0',     # Mint
    'temporal': '#E8A87C',      # Peach
    'perspectival': '#C38D9E',  # Mauve
    'conditional': '#41B3A3',   # Teal
    'stochastic': '#F4A261',    # Orange
    'optimization': '#7209B7',  # Purple
    'negotiation': '#F72585',   # Magenta
    'definitional': '#4CC9F0',  # Sky blue

    # Validity score colors
    'valid': '#2ECC71',         # Green (≥0.7)
    'marginal': '#F39C12',      # Amber (0.5-0.7)
    'invalid': '#E74C3C',       # Red (<0.5)

    # UI elements
    'bread': '#F5DEB3',         # Wheat
    'filling': '#FF6B6B',       # Vibrant red
    'background': '#FAFAFA',    # Off-white
    'text': '#2C3E50',          # Dark blue-gray
    'accent': '#3498DB',        # Bright blue
}


def get_structural_type_color(structural_type: str) -> str:
    """Get color for a structural type.

    Args:
        structural_type: Name of structural type (e.g., 'bound', 'dialectic')

    Returns:
        Hex color code, defaults to accent color if type not found
    """
    return COLORS.get(structural_type.lower(), COLORS['accent'])


def get_validity_color(validity_score: float) -> str:
    """Get color for a validity score.

    Args:
        validity_score: Validity score (0.0-1.0)

    Returns:
        Hex color code based on thresholds:
        - Green for ≥0.7 (valid)
        - Amber for 0.5-0.7 (marginal)
        - Red for <0.5 (invalid)
    """
    if validity_score >= 0.7:
        return COLORS['valid']
    elif validity_score >= 0.5:
        return COLORS['marginal']
    else:
        return COLORS['invalid']
