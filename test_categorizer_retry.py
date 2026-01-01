#!/usr/bin/env python3
"""
Quick test to verify retry logic and invalid category handling.
"""
import os
from claude_categorizer import categorize_with_retry

# Test with known problematic titles and variations
test_titles = [
    "Google delays when Chrome will phase out third-party cookies to 2024",  # Should be Security/Privacy, not Privacy/Security
    "Amazon launches new retail partnership with Whole Foods",  # Should be E-commerce/Retail, not Retail/E-commerce
    "FTC proposes new data privacy regulations",  # Could be Regulation/Policy OR Security/Privacy
    "Tesla unveils new self-driving features",  # Should be Automotive/Mobility
]

def test_retry_logic():
    """Test that retry logic handles invalid categories."""
    print("Testing categorizer with retry logic...")
    print("=" * 80)

    # Check for API key
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print("ERROR: ANTHROPIC_API_KEY not set")
        print("Set your API key: export ANTHROPIC_API_KEY='your-key'")
        return

    try:
        results = categorize_with_retry(test_titles, model='claude-3-5-haiku-20241022')

        print("\nResults:")
        for title, category in results.items():
            print(f"  Title: {title}")
            print(f"  Category: {category}")
            print()

        print("✓ Test passed - all categories valid")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_retry_logic()

    print("\nCheck 'invalid_categories.log' for any logged attempts")
