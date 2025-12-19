#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown parser for The Ride Home links.
Extracts date headers and bulleted links from markdown files.
"""
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


def parse_date_header(line: str) -> Optional[datetime]:
    """
    Parse date from markdown header.

    Formats supported:
        **Friday, December 12 2025 - Title**
        **Friday, December 05 2025**
        **Friday, December 05** (requires year from context)

    Args:
        line: Markdown line to parse

    Returns:
        datetime object or None if not a date header
    """
    # Pattern: **DayOfWeek, Month Day Year - Optional Title**
    pattern = r'\*\*(\w+day),\s+(\w+)\s+(\d{1,2})\s+(\d{4})'
    match = re.search(pattern, line)

    if match:
        # Extract components (ignore day of week)
        _, month_name, day, year = match.groups()

        # Parse into datetime
        date_str = f"{month_name} {day} {year}"
        try:
            return datetime.strptime(date_str, "%B %d %Y")
        except ValueError:
            return None

    return None


def parse_date_header_no_year(line: str, year: int) -> Optional[datetime]:
    """
    Parse date header without year (longreads format).

    Format: **Friday, December 05**

    Args:
        line: Markdown line to parse
        year: Year to use for date

    Returns:
        datetime object or None if not a date header
    """
    # Pattern: **DayOfWeek, Month Day**
    pattern = r'\*\*(\w+day),\s+(\w+)\s+(\d{1,2})\*\*'
    match = re.search(pattern, line)

    if match:
        # Extract components
        _, month_name, day = match.groups()

        # Parse with provided year
        date_str = f"{month_name} {day} {year}"
        try:
            return datetime.strptime(date_str, "%B %d %Y")
        except ValueError:
            return None

    return None


def parse_link_bullet(line: str) -> Optional[Dict[str, str]]:
    """
    Parse a markdown link bullet into title, url, source.

    Formats supported:
        * [Title](url) (Source)
        * [Title](url)(Source)
        * [Title](url)

    Args:
        line: Markdown bullet line

    Returns:
        Dict with 'title', 'url', 'source' or None if not a valid bullet
    """
    # Pattern: * [title](url) optional(source)
    # Handle both " (Source)" and "(Source)" without space
    pattern = r'\*\s+\[([^\]]+)\]\(([^\)]+)\)\s*(?:\(([^\)]+)\))?'
    match = re.search(pattern, line)

    if match:
        title, url, source = match.groups()
        return {
            'title': title.strip(),
            'url': url.strip(),
            'source': source.strip() if source else None
        }

    return None


def extract_year_from_filename(filename: str) -> Optional[int]:
    """
    Extract year from filename like 'longreads-2024.md' or 'all-links-2023.md'.

    Args:
        filename: Filename to parse

    Returns:
        Year as integer or None if not found
    """
    pattern = r'-(\d{4})\.md$'
    match = re.search(pattern, filename)
    if match:
        return int(match.group(1))
    return None


def parse_showlinks_file(file_path: str) -> List[Dict]:
    """
    Parse a showlinks markdown file into structured entries.

    Args:
        file_path: Path to markdown file

    Returns:
        List of dicts with keys: date, title, url, source, episode_date
    """
    entries = []
    current_date = None

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # Try to parse as date header
            date = parse_date_header(line)
            if date:
                current_date = date
                continue

            # Try to parse as link bullet
            if current_date and line.startswith('*'):
                link = parse_link_bullet(line)
                if link:
                    entries.append({
                        'date': current_date,
                        'title': link['title'],
                        'url': link['url'],
                        'source': link['source'],
                        'episode_date': current_date  # Same as date for now
                    })

    return entries


def parse_longreads_file(file_path: str) -> List[Dict]:
    """
    Parse a longreads markdown file into structured entries.
    Handles date headers both with and without years.

    Args:
        file_path: Path to markdown file

    Returns:
        List of dicts with keys: date, title, url, source, episode_date
    """
    entries = []
    current_date = None

    # Extract year from filename for dates without year
    filename = Path(file_path).name
    file_year = extract_year_from_filename(filename)

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # Try to parse as date header WITH year first
            date = parse_date_header(line)
            if date:
                current_date = date
                continue

            # Try to parse as date header WITHOUT year
            if file_year:
                date = parse_date_header_no_year(line, file_year)
                if date:
                    current_date = date
                    continue

            # Try to parse as link bullet
            if current_date and line.startswith('*'):
                link = parse_link_bullet(line)
                if link:
                    entries.append({
                        'date': current_date,
                        'title': link['title'],
                        'url': link['url'],
                        'source': link['source'],
                        'episode_date': current_date
                    })

    return entries


if __name__ == '__main__':
    # Test parsing on real file
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]

        if 'longreads' in file_path:
            entries = parse_longreads_file(file_path)
        else:
            entries = parse_showlinks_file(file_path)

        print(f"Parsed {len(entries)} links from {file_path}")
        print("\nFirst 3 entries:")
        for entry in entries[:3]:
            print(f"  {entry['date'].strftime('%Y-%m-%d')}: {entry['title'][:50]}... ({entry['source']})")
