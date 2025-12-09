#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extract Friday episodes with Weekend Longreads to analyze the pattern
"""

import feedparser
import time
import re
from bs4 import BeautifulSoup


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
    print("Analyzing Friday episodes with Weekend Longreads...")
    print("=" * 60)

    feed = feedparser.parse('ridehome.rss')

    friday_longreads = []

    for entry in feed.entries:
        # Check if it's a Friday
        day_of_week = time.strftime("%A", entry.published_parsed)

        if day_of_week == "Friday":
            html_content = extract_content_encoded(entry)
            if html_content:
                # Check for Weekend Longreads
                soup = BeautifulSoup(html_content, 'html5lib')
                longreads_block = soup.find_all("p", string=re.compile("Weekend Longreads|Longreads|Suggestions"))

                if longreads_block:
                    friday_longreads.append({
                        'title': entry.get('title', 'No title'),
                        'date': time.strftime("%A, %B %d %Y", entry.published_parsed),
                        'html': html_content
                    })

    print(f"Found {len(friday_longreads)} Friday episodes with Longreads\n")

    # Show first 5 examples
    print("SAMPLE FRIDAY LONGREADS EPISODES")
    print("=" * 60)

    for i, episode in enumerate(friday_longreads[:5], 1):
        print(f"\n{i}. {episode['title']}")
        print(f"   Date: {episode['date']}")

        # Extract just the Longreads section
        soup = BeautifulSoup(episode['html'], 'html5lib')
        longreads_p = soup.find("p", string=re.compile("Weekend Longreads|Longreads|Suggestions"))

        if longreads_p:
            print(f"   Section header: {longreads_p.get_text()}")

            # Get the next sibling (should be <ul>)
            sibling = longreads_p.next_sibling
            from bs4 import NavigableString
            while sibling and isinstance(sibling, NavigableString):
                sibling = sibling.next_sibling

            if sibling and sibling.name == 'ul':
                links = sibling.find_all('a')
                print(f"   Number of links: {len(links)}")
                if links:
                    print(f"   First link: {links[0].get_text()}")

            # Show a snippet of the HTML
            print(f"\n   HTML snippet:")
            snippet = str(longreads_p) + '\n' + str(sibling)[:300] if sibling else str(longreads_p)
            print(f"   {snippet[:400]}...")

    # Save first 3 examples for test fixtures
    print("\n" + "=" * 60)
    print("Saving examples for test fixtures...")

    import json
    test_fixtures = {}

    for i, episode in enumerate(friday_longreads[:3], 1):
        soup = BeautifulSoup(episode['html'], 'html5lib')
        longreads_p = soup.find("p", string=re.compile("Weekend Longreads|Longreads|Suggestions"))

        if longreads_p:
            # Get paragraph + next ul
            sibling = longreads_p.next_sibling
            from bs4 import NavigableString
            while sibling and isinstance(sibling, NavigableString):
                sibling = sibling.next_sibling

            html_snippet = str(longreads_p) + '\n' + str(sibling) if sibling else str(longreads_p)

            test_fixtures[f'friday_longreads_{i}'] = {
                'title': episode['title'],
                'date': episode['date'],
                'html': html_snippet
            }

    with open('friday_longreads_samples.json', 'w', encoding='utf-8') as f:
        json.dump(test_fixtures, f, indent=2, ensure_ascii=False)

    print("✓ Saved to friday_longreads_samples.json")


if __name__ == '__main__':
    main()
