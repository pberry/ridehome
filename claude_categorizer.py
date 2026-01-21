#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proof-of-concept: Use Claude API to categorize topics instead of keyword matching.

This demonstrates how to integrate with Claude API for intelligent topic categorization.
Requires: pip install anthropic python-dotenv
"""
import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict
from dotenv import load_dotenv
from categories import TOPIC_CATEGORIES

# Load environment variables from .env file
load_dotenv()


class InvalidCategoryError(Exception):
    """Raised when Claude returns a category not in the valid list."""
    def __init__(self, invalid_categories: Dict[str, str]):
        """
        Args:
            invalid_categories: Dict mapping title -> invalid category
        """
        self.invalid_categories = invalid_categories
        super().__init__(f"Found {len(invalid_categories)} invalid categories")


def log_invalid_category(title: str, attempted_category: str, final_category: str = None, log_file: str = 'invalid_categories.log'):
    """
    Log invalid category attempts for review.

    This helps identify:
    - New categories that should be added (e.g., "Quantum Computing")
    - Transposed categories that need better prompting (e.g., "Privacy/Security" vs "Security/Privacy")

    Args:
        title: The article title being categorized
        attempted_category: The invalid category the AI tried to use
        final_category: The category used after retry (None if still processing)
        log_file: Path to log file
    """
    timestamp = datetime.now().isoformat()

    with open(log_file, 'a', encoding='utf-8') as f:
        if final_category:
            f.write(f"{timestamp} | RESOLVED | {attempted_category} → {final_category} | {title}\n")
        else:
            f.write(f"{timestamp} | ATTEMPTED | {attempted_category} | {title}\n")


def normalize_title(title: str) -> str:
    """
    Normalize title by converting smart quotes to straight quotes,
    converting em-dashes/en-dashes to regular hyphens,
    and removing escaped characters that cause JSON parsing issues.
    """
    # Use Unicode escapes to ensure correct character matching
    # U+2018 = LEFT SINGLE QUOTATION MARK
    # U+2019 = RIGHT SINGLE QUOTATION MARK
    # U+201C = LEFT DOUBLE QUOTATION MARK
    # U+201D = RIGHT DOUBLE QUOTATION MARK
    # U+2013 = EN DASH
    # U+2014 = EM DASH
    normalized = (title
            .replace('\u2018', "'")  # '
            .replace('\u2019', "'")  # '
            .replace('\u201c', '"')  # "
            .replace('\u201d', '"')  # "
            .replace('\u2013', '-')  # – (en-dash)
            .replace('\u2014', '-')) # — (em-dash)

    # Remove escaped characters (e.g., \| becomes |, \. becomes .)
    # These are HTML/Markdown escapes that break JSON
    normalized = normalized.replace('\\|', '|')  # Escaped pipe
    normalized = normalized.replace('\\.', '.')  # Escaped period
    normalized = normalized.replace('\\-', '-')  # Escaped dash
    normalized = normalized.replace('\\#', '#')  # Escaped hash
    normalized = normalized.replace('\\*', '*')  # Escaped asterisk
    normalized = normalized.replace('\\(', '(')  # Escaped parens
    normalized = normalized.replace('\\)', ')')
    normalized = normalized.replace('\\[', '[')  # Escaped brackets
    normalized = normalized.replace('\\]', ']')

    return normalized


def create_categorization_prompt(titles: List[str], retry_count: int = 0) -> str:
    """
    Create the system prompt for Claude API.

    This is designed to match the existing categorization scheme
    while allowing for more nuanced understanding.

    Args:
        titles: List of titles to categorize (not used in prompt, but kept for API consistency)
        retry_count: Number of previous attempts (increases strictness)
    """
    categories_list = "\n".join(f"- {cat}" for cat in TOPIC_CATEGORIES)

    # Base prompt
    system_prompt = f"""You are analyzing tech news article titles from The Ride Home podcast.
Your task is to categorize each title into ONE of these topic categories:

{categories_list}

CRITICAL: You MUST use these EXACT category strings. Do not create variations.
- Use "Security/Privacy" NOT "Privacy/Security"
- Use "E-commerce/Retail" NOT "Retail/E-commerce"
- Use "Regulation/Policy" NOT "Policy/Regulation"
- The order of words matters - copy the exact string from the list above

Guidelines:
- Choose the MOST specific category that fits
- If multiple categories could apply, pick the primary focus
- Use "Other Tech News" only if none of the categories fit
- Consider the main subject, not just keyword matches
- Look at context: "Tesla lawsuit" → Regulation/Policy, not Automotive

CRITICAL JSON FORMATTING:
- Use ONLY double quotes (") for JSON strings, NEVER single quotes (')
- Escape backslashes: \\ becomes \\\\
- Escape double quotes inside strings: " becomes \\"
- Titles may contain: apostrophes ('Pay'), backslashes (\\|), special chars
- Example: {{"title": "Apple's \\\\ Microsoft deal", "category": "Hardware/Chips"}}
- Correct: {{"title": "Apple's new iPhone", "category": "Hardware/Chips"}}
- Wrong: {{'title': 'Apple's new iPhone', 'category': 'Hardware/Chips'}}

Be consistent and accurate. Focus on the primary topic of each article."""

    # Add stronger enforcement on retries
    if retry_count > 0:
        system_prompt += f"""

WARNING: Previous attempt returned invalid categories. This is retry #{retry_count}.
You MUST use ONLY the exact category strings listed above. NO variations allowed."""

    return system_prompt


def create_user_prompt(titles: List[str]) -> str:
    """Create user message with titles to categorize."""
    # Normalize titles to use straight quotes
    normalized_titles = [normalize_title(t) for t in titles]
    titles_numbered = "\n".join(f"{i+1}. {title}" for i, title in enumerate(normalized_titles))

    return f"""Categorize these {len(titles)} tech news titles and return ONLY a JSON array.

Titles to categorize:
{titles_numbered}

Return ONLY this JSON structure with NO additional text or explanation:
[
  {{"title": "exact title text", "category": "Category Name"}},
  {{"title": "exact title text", "category": "Category Name"}}
]

Requirements:
- Return ONLY the JSON array, nothing else
- No markdown code blocks
- No explanations or commentary
- Maintain exact order (1-{len(titles)})
- Use exact title text from above
- Use exact category names from the system prompt"""


def categorize_with_claude(titles: List[str], api_key: str = None, model: str = 'claude-haiku-4-5-20251001', retry_count: int = 0) -> Dict[str, str]:
    """
    Categorize titles using Claude API.

    Args:
        titles: List of article titles to categorize
        api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
        model: Model to use (haiku for cost efficiency, sonnet for quality)

    Returns:
        Dictionary mapping ORIGINAL title to category (preserves smart quotes from input)
    """
    try:
        import anthropic
    except ImportError:
        raise ImportError("Install anthropic package: pip install anthropic")

    # Get API key from environment if not provided
    if api_key is None:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("Set ANTHROPIC_API_KEY environment variable or pass api_key parameter")

    client = anthropic.Anthropic(api_key=api_key)

    # Create mapping from normalized to original titles
    title_map = {normalize_title(t): t for t in titles}

    # Create prompts (will normalize titles internally)
    system_prompt = create_categorization_prompt(titles, retry_count=retry_count)
    user_prompt = create_user_prompt(titles)

    # Call Claude API with assistant prefill to force JSON output
    # The assistant prefill technique ensures Claude starts with JSON
    message = client.messages.create(
        model=model,
        max_tokens=8000,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": "["}  # Prefill to force JSON array
        ]
    )

    # Parse response
    # The assistant prefill "[" means Claude continues from there
    # So we need to prepend it to get complete JSON
    raw_response = message.content[0].text

    # If response already starts with "[", don't prepend (Claude included it)
    # Otherwise, prepend the "[" from our prefill
    if raw_response.strip().startswith('['):
        response_text = raw_response
    else:
        response_text = "[" + raw_response

    # Debug: print raw response if parsing fails
    try:
        # Extract JSON from response (handle multiple formats)
        json_text = response_text.strip()

        # Handle markdown code blocks
        if '```json' in json_text:
            json_text = json_text.split('```json')[1].split('```')[0].strip()
        elif '```' in json_text:
            json_text = json_text.split('```')[1].split('```')[0].strip()

        categorizations = json.loads(json_text)
    except json.JSONDecodeError as e:
        print("\n" + "=" * 80)
        print("ERROR: Failed to parse Claude's response as JSON")
        print("=" * 80)
        print("\nRaw response from Claude:")
        print("-" * 80)
        print(response_text[:500])  # First 500 chars
        if len(response_text) > 500:
            print(f"\n... ({len(response_text) - 500} more characters) ...\n")
            print(response_text[-500:])  # Last 500 chars
        print("-" * 80)
        print(f"\nJSON Error: {e}")
        print(f"Attempted to parse {len(json_text)} characters")
        print(f"JSON starts with: {repr(json_text[:50])}")
        print(f"JSON ends with: {repr(json_text[-50:])}")
        print("\nThis usually means Claude didn't return valid JSON.")
        print("The response format may need adjustment.")
        raise

    # Convert to dictionary, mapping back to original titles
    result = {}
    invalid_categories = {}

    for item in categorizations:
        # Claude returns normalized titles (straight quotes)
        normalized_title = item['title']
        category = item['category']

        # Validate category is recognized
        if category not in TOPIC_CATEGORIES:
            # Map back to original title for error reporting
            original_title = title_map.get(normalized_title, normalized_title)
            invalid_categories[original_title] = category
            # Log the invalid attempt
            log_invalid_category(original_title, category)
        else:
            # Map back to original title (with smart quotes if present)
            original_title = title_map.get(normalized_title, normalized_title)
            result[original_title] = category

    # If any invalid categories found, raise exception for retry
    if invalid_categories:
        raise InvalidCategoryError(invalid_categories)

    return result


def categorize_with_retry(titles: List[str], api_key: str = None, model: str = 'claude-haiku-4-5-20251001', max_retries: int = 3) -> Dict[str, str]:
    """
    Categorize titles with automatic retry on invalid categories.

    Args:
        titles: List of article titles to categorize
        api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
        model: Model to use (haiku for cost efficiency, sonnet for quality)
        max_retries: Maximum number of retry attempts

    Returns:
        Dictionary mapping title to category

    Raises:
        InvalidCategoryError: If invalid categories persist after max_retries
    """
    last_error = None

    for attempt in range(max_retries):
        try:
            result = categorize_with_claude(titles, api_key=api_key, model=model, retry_count=attempt)

            # Success! Log any previous failures as resolved
            if last_error and attempt > 0:
                for title, invalid_cat in last_error.invalid_categories.items():
                    final_cat = result.get(title, 'Unknown')
                    log_invalid_category(title, invalid_cat, final_category=final_cat)

            return result

        except InvalidCategoryError as e:
            last_error = e
            if attempt < max_retries - 1:
                print(f"\nRetry {attempt + 1}/{max_retries - 1}: Found {len(e.invalid_categories)} invalid categories")
                print(f"Invalid: {list(e.invalid_categories.values())}")
                print("Retrying with stricter prompt...\n")
            else:
                # Final attempt failed
                print(f"\nFailed after {max_retries} attempts. Invalid categories:")
                for title, category in e.invalid_categories.items():
                    print(f"  - '{category}' for: {title[:80]}")
                raise

    # Should never reach here, but for type safety
    raise last_error


def get_uncategorized_titles(db_path: str, months: int = 1) -> List[str]:
    """
    Get titles from the last N months that need categorization.

    In a real implementation, you'd track which titles have been
    categorized by Claude vs keyword matching.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cutoff = datetime.now() - timedelta(days=30 * months)
    cutoff_unix = int(cutoff.timestamp())

    cursor.execute("""
        SELECT DISTINCT title
        FROM links
        WHERE date_unix >= ? AND title IS NOT NULL
        ORDER BY date_unix DESC
    """, (cutoff_unix,))

    titles = [row[0] for row in cursor.fetchall()]
    conn.close()

    return titles


def batch_categorize(titles: List[str], batch_size: int = 100, **kwargs) -> Dict[str, str]:
    """
    Categorize titles in batches to manage token usage.

    For large datasets, process in chunks to:
    - Reduce per-request token overhead
    - Allow progress tracking
    - Handle API rate limits
    """
    results = {}

    for i in range(0, len(titles), batch_size):
        batch = titles[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}: titles {i+1}-{min(i+batch_size, len(titles))}")

        batch_results = categorize_with_retry(batch, **kwargs)
        results.update(batch_results)

    return results


def demo_comparison(db_path: str = 'ridehome.db', sample_size: int = 20):
    """
    Demo: Compare keyword matching vs Claude API categorization.

    This is for evaluation purposes only - requires ANTHROPIC_API_KEY.
    """
    from status_generator import categorize_topic  # Import existing function

    # Get recent titles
    titles = get_uncategorized_titles(db_path, months=1)[:sample_size]

    print(f"Comparing categorization methods on {len(titles)} recent titles")
    print("=" * 100)

    # Check for API key
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print("\nWARNING: ANTHROPIC_API_KEY not set. Skipping Claude API comparison.")
        print("To run this demo, set your API key:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        print("\nShowing keyword-based categorization only:\n")

        for i, title in enumerate(titles, 1):
            keyword_category = categorize_topic(title)
            print(f"{i:2}. {title[:80]}")
            print(f"    Keyword: {keyword_category}")
            print()
        return

    # Get Claude categorization
    print("\nCalling Claude API...")
    claude_results = categorize_with_retry(titles, model='claude-haiku-4-5-20251001')

    # Compare results
    print("\nComparison Results:")
    print("=" * 100)

    agreements = 0
    disagreements = 0

    for i, title in enumerate(titles, 1):
        keyword_category = categorize_topic(title)
        claude_category = claude_results.get(title, 'Unknown')

        match = keyword_category == claude_category
        if match:
            agreements += 1
        else:
            disagreements += 1

        print(f"{i:2}. {title[:80]}")
        print(f"    Keyword: {keyword_category}")
        print(f"    Claude:  {claude_category} {'✓' if match else '✗'}")
        print()

    print("=" * 100)
    print(f"Agreement: {agreements}/{len(titles)} ({100*agreements/len(titles):.1f}%)")
    print(f"Disagreement: {disagreements}/{len(titles)} ({100*disagreements/len(titles):.1f}%)")
    print()
    print("Note: Disagreements don't necessarily mean errors - Claude may provide")
    print("more nuanced categorization than simple keyword matching.")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--demo':
        sample_size = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        demo_comparison(sample_size=sample_size)
    else:
        print(__doc__)
        print("\nUsage:")
        print("  python3 claude_categorizer.py --demo [sample_size]")
        print("\nExample:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        print("  python3 claude_categorizer.py --demo 20")
