#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test normalize_title with problematic characters."""
import json
from claude_categorizer import normalize_title

# Test cases with problematic Unicode characters (using escapes)
test_cases = [
    "A damn stupid thing to do\u2014the origins of C",  # em-dash
    "Apple\u2019s new iPhone \u2013 a review",  # en-dash + smart quote
    "The \u201cbest\u201d product ever",  # smart double quotes
    "It\u2019s not what you think",  # smart single quote
]

print("Testing normalize_title():")
print("=" * 80)

for original in test_cases:
    normalized = normalize_title(original)
    print(f"\nOriginal:   {original}")
    print(f"Normalized: {normalized}")
    
    # Test if it can be JSON-serialized
    try:
        test_obj = {"title": normalized, "category": "Other Tech News"}
        json_str = json.dumps(test_obj)
        parsed = json.loads(json_str)
        print(f"JSON:       ✓ Valid")
    except json.JSONDecodeError as e:
        print(f"JSON:       ✗ FAILED - {e}")

print("\n" + "=" * 80)
print("✓ All tests completed")
