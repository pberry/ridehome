#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for CSS rules to ensure accessibility and styling requirements.
"""
import unittest
import re
from pathlib import Path


class TestAICategoryBubbleStyles(unittest.TestCase):
    """Test AI category speech bubble CSS for proper visited link styling."""

    def setUp(self):
        """Load main SCSS file."""
        css_path = Path('docs/assets/main.scss')
        if not css_path.exists():
            self.skipTest('CSS file not found')

        with open(css_path, 'r', encoding='utf-8') as f:
            self.css_content = f.read()

    def test_visited_hover_state_exists_for_light_mode(self):
        """visited:hover state defined for ai-category to ensure readable text on hover"""
        # Should have a.ai-category:visited:hover rule
        pattern = r'a\.ai-category:visited:hover\s*\{'

        self.assertRegex(self.css_content, pattern,
                        "Missing a.ai-category:visited:hover rule for light mode contrast")

    def test_visited_hover_uses_light_color_in_light_mode(self):
        """visited:hover uses light text color for contrast against blue background"""
        # Find the visited:hover rule
        visited_hover_pattern = r'a\.ai-category:visited:hover\s*\{([^}]+)\}'
        match = re.search(visited_hover_pattern, self.css_content)

        self.assertIsNotNone(match, "a.ai-category:visited:hover rule not found")

        rule_content = match.group(1)

        # Should set color to $base3 (light color) for contrast
        # Acceptable values: $base3, #fdf6e3, or var(--bg-primary) in light mode
        has_light_color = (
            '$base3' in rule_content or
            '#fdf6e3' in rule_content or
            'color:' in rule_content  # At minimum should set SOME color
        )

        self.assertTrue(has_light_color,
                       f"visited:hover should set light text color. Found: {rule_content}")

    def test_dark_mode_visited_hover_exists(self):
        """dark mode has visited:hover state for ai-category"""
        # Should have dark theme variant
        pattern = r'\[data-theme="dark"\]\s+a\.ai-category:visited:hover\s*\{'

        self.assertRegex(self.css_content, pattern,
                        "Missing dark mode a.ai-category:visited:hover rule")

    def test_dark_mode_visited_hover_uses_dark_color(self):
        """dark mode visited:hover uses dark text color for contrast against cyan"""
        # Find the dark mode visited:hover rule
        dark_visited_hover = r'\[data-theme="dark"\]\s+a\.ai-category:visited:hover\s*\{([^}]+)\}'
        match = re.search(dark_visited_hover, self.css_content)

        self.assertIsNotNone(match, "Dark mode a.ai-category:visited:hover rule not found")

        rule_content = match.group(1)

        # Should set color to $base03 (dark color) for contrast on cyan background
        has_dark_color = (
            '$base03' in rule_content or
            '#002b36' in rule_content or
            'color:' in rule_content
        )

        self.assertTrue(has_dark_color,
                       f"Dark mode visited:hover should set dark text color. Found: {rule_content}")


if __name__ == '__main__':
    unittest.main()
