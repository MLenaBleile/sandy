"""Tests for dashboard components.

Tests color palette, helper functions, and component logic.
"""

import pytest
import sys
from pathlib import Path

# Add dashboard to path
dashboard_dir = Path(__file__).parent.parent.parent / "dashboard"
sys.path.insert(0, str(dashboard_dir))

from components.colors import (
    COLORS,
    get_structural_type_color,
    get_validity_color
)


class TestColorPalette:
    """Test color palette completeness and helper functions."""

    def test_all_structural_types_have_colors(self):
        """Verify all 10 structural types have assigned colors."""
        structural_types = [
            'bound', 'dialectic', 'epistemic', 'temporal', 'perspectival',
            'conditional', 'stochastic', 'optimization', 'negotiation', 'definitional'
        ]

        for type_name in structural_types:
            assert type_name in COLORS, f"Missing color for {type_name}"
            assert COLORS[type_name].startswith('#'), f"Invalid color format for {type_name}"

    def test_validity_colors_exist(self):
        """Verify validity score colors are defined."""
        assert 'valid' in COLORS
        assert 'marginal' in COLORS
        assert 'invalid' in COLORS

    def test_ui_colors_exist(self):
        """Verify UI element colors are defined."""
        ui_colors = ['bread', 'filling', 'background', 'text', 'accent']

        for color in ui_colors:
            assert color in COLORS, f"Missing UI color: {color}"

    def test_get_validity_color_valid(self):
        """Test validity color assignment for valid scores (≥0.7)."""
        assert get_validity_color(0.7) == COLORS['valid']
        assert get_validity_color(0.8) == COLORS['valid']
        assert get_validity_color(0.95) == COLORS['valid']
        assert get_validity_color(1.0) == COLORS['valid']

    def test_get_validity_color_marginal(self):
        """Test validity color assignment for marginal scores (0.5-0.7)."""
        assert get_validity_color(0.5) == COLORS['marginal']
        assert get_validity_color(0.6) == COLORS['marginal']
        assert get_validity_color(0.69) == COLORS['marginal']

    def test_get_validity_color_invalid(self):
        """Test validity color assignment for invalid scores (<0.5)."""
        assert get_validity_color(0.0) == COLORS['invalid']
        assert get_validity_color(0.3) == COLORS['invalid']
        assert get_validity_color(0.49) == COLORS['invalid']

    def test_get_structural_type_color_known_type(self):
        """Test color retrieval for known structural types."""
        assert get_structural_type_color('bound') == COLORS['bound']
        assert get_structural_type_color('dialectic') == COLORS['dialectic']
        assert get_structural_type_color('stochastic') == COLORS['stochastic']

    def test_get_structural_type_color_unknown_type(self):
        """Test fallback color for unknown structural type."""
        unknown_color = get_structural_type_color('unknown_type')
        assert unknown_color == COLORS['accent'], "Should fall back to accent color"

    def test_get_structural_type_color_case_insensitive(self):
        """Test that type matching is case-insensitive."""
        assert get_structural_type_color('BOUND') == COLORS['bound']
        assert get_structural_type_color('Dialectic') == COLORS['dialectic']


class TestSandwichCard:
    """Test sandwich card component logic."""

    def test_sandwich_card_renders_without_error(self):
        """Test that sandwich_card function executes without errors."""
        from components.sandwich_card import validity_badge

        # Test validity badge generation
        badge_html = validity_badge(0.85)

        assert '0.85' in badge_html
        assert 'background' in badge_html
        assert COLORS['valid'] in badge_html

    def test_validity_badge_colors(self):
        """Test that validity badges use correct colors."""
        from components.sandwich_card import validity_badge

        # Valid score
        badge_valid = validity_badge(0.9)
        assert COLORS['valid'] in badge_valid

        # Marginal score
        badge_marginal = validity_badge(0.6)
        assert COLORS['marginal'] in badge_marginal

        # Invalid score
        badge_invalid = validity_badge(0.3)
        assert COLORS['invalid'] in badge_invalid


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
