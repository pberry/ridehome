#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTML Content Parser

Shared module for parsing HTML content from RSS feeds.
Extracts structured sections (Links, Longreads, Sponsors, etc.) from HTML.
"""

import re
from bs4 import BeautifulSoup, NavigableString


def find_section(html, pattern):
    """
    Find and return a section from HTML content by pattern.

    Args:
        html: HTML string to parse
        pattern: Regex pattern to match in paragraph text (e.g., "Links", "Weekend Longreads")

    Returns:
        BeautifulSoup Tag element (typically <ul>) that follows the matching paragraph,
        or None if no match found
    """
    soup = BeautifulSoup(html, 'html5lib')
    section_block = soup.find_all("p", string=re.compile(pattern))

    if len(section_block) > 0:
        # Find all paragraphs whose next sibling is a <ul> (structural check)
        paragraphs_with_ul = []
        for paragraph in section_block:
            sibling = paragraph.next_sibling
            # Skip NavigableString nodes (whitespace) to find actual Tag
            while sibling and isinstance(sibling, NavigableString):
                sibling = sibling.next_sibling

            # If next sibling is a <ul>, add to candidates
            if sibling and sibling.name == 'ul':
                paragraphs_with_ul.append((paragraph, sibling))

        # Among candidates, choose shortest paragraph (header vs intro)
        if paragraphs_with_ul:
            shortest_paragraph, ul_element = min(paragraphs_with_ul, key=lambda item: len(item[0].get_text()))
            return ul_element

        # Fallback: if no paragraph has <ul> as next sibling, return None
        return None

    return None


def find_links_section(html):
    """
    Find and return the links section from HTML content.

    Tries to find explicit "Links:" paragraph first.
    Falls back to returning single <ul> if no "Links:" paragraph exists.

    Args:
        html: HTML string to parse

    Returns:
        BeautifulSoup Tag element (<ul>) containing links,
        or None if no links found or multiple <ul> blocks exist
    """
    # Try to find explicit "Links" section
    result = find_section(html, pattern="Links")
    if result:
        return result

    # Fallback: if no Links section, return first <ul> (assume it's show links)
    soup = BeautifulSoup(html, 'html5lib')
    uls = soup.find_all("ul")
    if uls:
        return uls[0]

    return None
