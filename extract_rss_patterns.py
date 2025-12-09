#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RSS Pattern Extraction Script

Analyzes ridehome.rss to identify different HTML patterns in content:encoded sections.
Categorizes episodes and extracts representative samples for test fixtures.
"""

import feedparser
import re
from bs4 import BeautifulSoup
from collections import defaultdict
import json


def analyze_html_content(html_content):
    """Analyze HTML content and categorize it by pattern"""
    if not html_content:
        return 'empty'

    soup = BeautifulSoup(html_content, 'html5lib')

    # Check for different patterns
    has_links_paragraph = bool(soup.find_all("p", string=re.compile("Links")))
    has_longreads = bool(soup.find_all("p", string=re.compile("Weekend Longreads")))
    has_sponsors = bool(soup.find_all("p", string=re.compile("Sponsors")))

    ul_elements = soup.find_all("ul")
    ul_count = len(ul_elements)

    # Categorize
    if has_links_paragraph and has_longreads:
        return 'links_and_longreads'
    elif has_links_paragraph and has_sponsors:
        return 'links_and_sponsors'
    elif has_links_paragraph:
        return 'links_only'
    elif has_longreads:
        return 'longreads_only'
    elif ul_count == 1:
        return 'single_ul_no_header'
    elif ul_count > 1:
        return 'multiple_ul_no_header'
    elif ul_count == 0:
        return 'no_links_at_all'
    else:
        return 'unknown'


def extract_content_encoded(entry):
    """Extract content:encoded from RSS entry"""
    if hasattr(entry, 'content') and len(entry.content) > 0:
        for content_block in entry.content:
            if content_block.get('type', '').lower() in ['text/html', 'html']:
                return content_block.value
        return entry.content[0].value
    elif hasattr(entry, 'summary'):
        return entry.summary
    return None


def main():
    print("Analyzing ridehome.rss...")
    print("=" * 60)

    # Parse RSS
    feed = feedparser.parse('ridehome.rss')

    if not feed.entries:
        print("ERROR: No entries found in RSS feed")
        return

    print(f"Total episodes in feed: {len(feed.entries)}\n")

    # Categorize all episodes
    categories = defaultdict(list)

    for i, entry in enumerate(feed.entries):
        title = entry.get('title', 'No title')
        html_content = extract_content_encoded(entry)
        category = analyze_html_content(html_content)

        categories[category].append({
            'index': i,
            'title': title,
            'html': html_content,
            'published': entry.get('published', 'Unknown date')
        })

    # Print distribution report
    print("PATTERN DISTRIBUTION")
    print("-" * 60)
    for category, episodes in sorted(categories.items(), key=lambda x: len(x[1]), reverse=True):
        count = len(episodes)
        percentage = (count / len(feed.entries)) * 100
        print(f"{category:30} {count:4} episodes ({percentage:5.1f}%)")

    print("\n" + "=" * 60)
    print("SAMPLE EPISODES BY CATEGORY")
    print("=" * 60)

    # Show samples from each category
    samples = {}
    for category, episodes in categories.items():
        print(f"\n{category.upper()}")
        print("-" * 60)

        # Show first 3 examples
        for ep in episodes[:3]:
            print(f"  [{ep['index']}] {ep['title']}")

        if len(episodes) > 3:
            print(f"  ... and {len(episodes) - 3} more")

        # Save first example as sample
        if episodes:
            samples[category] = {
                'title': episodes[0]['title'],
                'published': episodes[0]['published'],
                'html': episodes[0]['html'][:500] + '...' if episodes[0]['html'] and len(episodes[0]['html']) > 500 else episodes[0]['html']
            }

    # Save samples to JSON file
    print("\n" + "=" * 60)
    print("Saving samples to rss_pattern_samples.json...")

    with open('rss_pattern_samples.json', 'w', encoding='utf-8') as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)

    print("✓ Samples saved")

    # Generate detailed report for most interesting categories
    print("\n" + "=" * 60)
    print("DETAILED ANALYSIS: NO_LINKS_AT_ALL")
    print("=" * 60)

    if 'no_links_at_all' in categories:
        print(f"Found {len(categories['no_links_at_all'])} episodes with no links\n")
        for ep in categories['no_links_at_all'][:5]:
            print(f"Title: {ep['title']}")
            print(f"Date:  {ep['published']}")
            if ep['html']:
                snippet = ep['html'][:200].replace('\n', ' ')
                print(f"HTML:  {snippet}...")
            else:
                print("HTML:  [None]")
            print()
    else:
        print("No episodes found with this pattern")

    print("\n" + "=" * 60)
    print("Analysis complete!")


if __name__ == '__main__':
    main()
