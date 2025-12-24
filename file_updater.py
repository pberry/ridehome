#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File updater utilities for detecting and inserting new entries into markdown files.
Shared between showlinks.py and longread.py.
"""

import re
import os
from datetime import datetime
import time


def parse_top_date(input_str, entry_type='showlinks', year_context=None):
    """
    Parse the top date from either a markdown file or a date string.

    Args:
        input_str: Either a file path or a date string (e.g., "**Monday, December 08 2025 - Title**")
        entry_type: 'showlinks' or 'longreads' (affects date format parsing)
        year_context: Year to use for longreads without year (optional)

    Returns:
        datetime object or None if no valid date found
    """
    # Check if input looks like a file path (contains / or ends with .md)
    if '/' in input_str or input_str.endswith('.md'):
        # Try as file path
        if os.path.isfile(input_str):
            return _parse_top_date_from_file(input_str, entry_type, year_context)
        else:
            # File doesn't exist
            return None
    else:
        # Treat as date string
        return _parse_date_string(input_str, entry_type, year_context)


def _parse_top_date_from_file(file_path, entry_type, year_context=None):
    """Parse top date from markdown file after AUTO-GENERATED marker"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for marker
        if '<!-- AUTO-GENERATED CONTENT BELOW -->' not in content:
            return None

        # Split at marker and get content after it
        parts = content.split('<!-- AUTO-GENERATED CONTENT BELOW -->')
        if len(parts) < 2:
            return None

        after_marker = parts[1]

        # Find first line starting with **
        lines = after_marker.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('**') and line.endswith('**'):
                # Found a date header
                return _parse_date_string(line, entry_type, year_context)

        return None

    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error parsing file {file_path}: {e}")
        return None


def _parse_date_string(date_str, entry_type, year_context=None):
    """Parse date from string like '**Monday, December 08 2025 - Title**' or '**Friday, December 05**'"""
    # Remove ** markers
    date_str = date_str.strip('*').strip()

    if entry_type == 'showlinks':
        # Format: "Monday, December 08 2025 - Title"
        # Extract date part before the dash
        if ' - ' in date_str:
            date_part = date_str.split(' - ')[0].strip()
        else:
            date_part = date_str.strip()

        # Parse: "Monday, December 08 2025"
        try:
            dt = datetime.strptime(date_part, "%A, %B %d %Y")
            return dt
        except ValueError as e:
            print(f"Error parsing showlinks date '{date_part}': {e}")
            return None

    elif entry_type == 'longreads':
        # Format could be:
        # - "Friday, December 05" (old format, needs year_context)
        # - "Friday, December 05 2025" (new format with year)

        date_str = date_str.strip()

        # Try with year first (new format)
        try:
            dt = datetime.strptime(date_str, "%A, %B %d %Y")
            return dt
        except ValueError:
            pass

        # Try without year (old format)
        try:
            # Determine which year to use
            if year_context is not None:
                year = year_context
            else:
                year = datetime.now().year

            # Parse with year added to avoid Python 3.15 deprecation warning
            # See: https://github.com/python/cpython/issues/70647
            date_with_year = f"{date_str} {year}"
            dt = datetime.strptime(date_with_year, "%A, %B %d %Y")
            return dt
        except ValueError as e:
            print(f"Error parsing longreads date '{date_str}': {e}")
            return None

    return None


def find_new_entries(feed_entries, top_date=None):
    """
    Filter feed entries to only those newer than top_date.

    Args:
        feed_entries: List of feedparser entry objects
        top_date: datetime object representing the most recent entry in the file
                  (None means return all entries)

    Returns:
        List of entries newer than top_date, in reverse chronological order (newest first)
    """
    if top_date is None:
        # No existing entries, return all
        return feed_entries

    new_entries = []
    # Convert top_date to date-only for comparison (ignore time)
    top_date_only = top_date.date()

    for entry in feed_entries:
        # Convert feed published_parsed to datetime
        entry_time = time.struct_time(entry['published_parsed'])
        entry_dt = datetime(*entry_time[:6])
        entry_date_only = entry_dt.date()

        # Only include if newer than top_date (compare dates only, not times)
        if entry_date_only > top_date_only:
            new_entries.append(entry)

    # Already in reverse chronological order from feed, but ensure it
    new_entries.sort(key=lambda e: datetime(*time.struct_time(e['published_parsed'])[:6]), reverse=True)

    return new_entries


def infer_year_from_context(file_path):
    """
    Infer year from file path like 'docs/longreads-2025.md'.
    Falls back to current year if no year found in path.

    Args:
        file_path: Path to markdown file

    Returns:
        Year as integer
    """
    # Extract year from filename pattern like "longreads-2025.md"
    match = re.search(r'-(\d{4})\.md', file_path)
    if match:
        return int(match.group(1))

    # Fallback to current year
    return datetime.now().year


def group_entries_by_year(entries):
    """
    Group feed entries by year.

    Args:
        entries: List of feed entries

    Returns:
        Dictionary mapping year (int) to list of entries for that year
    """
    groups = {}
    for entry in entries:
        year = entry['published_parsed'].tm_year
        if year not in groups:
            groups[year] = []
        groups[year].append(entry)

    return groups
