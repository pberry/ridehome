#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate year-based markdown pages from database.
Creates all-links-YYYY.md and longreads-YYYY.md files.
Uses hash-based comparison to skip unchanged files.
"""
import sqlite3
import hashlib
import os
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

PACIFIC_TZ = ZoneInfo("America/Los_Angeles")

# Configuration for each page type
PAGE_CONFIGS = {
    'showlinks': {
        'output_prefix': 'all-links',
        'link_type': 'showlink',
        'header_template': 'showlinks-header.md',
        'deprecation_notice': "[The Ride Home](https://www.ridehome.info/podcast/techmeme-ride-home/) now has a proper web site and [RSS feed](https://feedly.com/i/subscription/feed/https://www.ridehome.info/rss/).",
        'header_spacing': '\n\n',  # Double newline after date header
        'frontmatter': None,
        'include_episode_title': True,  # Show episode titles for showlinks
    },
    'longreads': {
        'output_prefix': 'longreads',
        'link_type': 'longread',
        'header_template': 'longreads-header.md',
        'deprecation_notice': None,
        'header_spacing': '\n',  # Single newline after date header
        'frontmatter': '---\ntitle: Weekend Longreads {year}\n---\n',
        'include_episode_title': False,  # No episode titles for longreads
    }
}


def get_available_years(db_path='ridehome.db'):
    """
    Query database for all years with data.

    Returns:
        dict: {link_type: [year1, year2, ...]}
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT link_type, strftime('%Y', date) as year
        FROM links
        GROUP BY link_type, year
        ORDER BY year DESC
    """)

    results = {}
    for link_type, year in cursor.fetchall():
        if link_type not in results:
            results[link_type] = []
        results[link_type].append(int(year))

    conn.close()
    return results


def get_links_for_year(db_path, year, link_type):
    """
    Query all links for a given year and type.

    Returns:
        list of dicts with keys: date, title, url, source, episode_title
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT date, title, url, source, episode_title
        FROM links
        WHERE link_type = ?
          AND strftime('%Y', date) = ?
        ORDER BY date DESC
    """, (link_type, str(year)))

    links = []
    for row in cursor.fetchall():
        links.append({
            'date': row[0],
            'title': row[1],
            'url': row[2],
            'source': row[3],
            'episode_title': row[4]
        })

    conn.close()
    return links


def format_date_header(date_str, year, episode_title=None, include_episode_title=False):
    """
    Format date header from ISO date string with optional episode title.

    Args:
        date_str: ISO format date string (YYYY-MM-DD)
        year: Year to include in output
        episode_title: Optional episode title to append
        include_episode_title: If True, include episode title in header

    Returns:
        str: Formatted header like "**Monday, January 06 2026 - Episode Title**"
    """
    dt = datetime.fromisoformat(date_str)
    header = f"**{dt.strftime('%A, %B %d')} {year}**"

    if include_episode_title and episode_title:
        header = f"**{dt.strftime('%A, %B %d')} {year} - {episode_title}**"

    return header


def group_links_by_date(links):
    """
    Group links by date.

    Returns:
        dict: {date_str: [link1, link2, ...]}
    """
    grouped = {}
    for link in links:
        date = link['date']
        if date not in grouped:
            grouped[date] = []
        grouped[date].append(link)

    return grouped


def generate_markdown_content(year, link_type, links, config):
    """
    Generate complete markdown content for a year page.

    Returns:
        str: Complete markdown file content
    """
    parts = []

    # Add frontmatter if specified
    if config['frontmatter']:
        parts.append(config['frontmatter'].format(year=year))
        parts.append('')

    # Add Jekyll include directive
    parts.append(f"{{% include_relative _includes/{config['header_template']} %}}")
    parts.append('')

    # Add deprecation notice if specified
    if config['deprecation_notice']:
        parts.append(config['deprecation_notice'])
        parts.append('')

    # Add AUTO-GENERATED marker
    parts.append('<!-- AUTO-GENERATED CONTENT BELOW -->')
    parts.append('')

    # Group links by date
    grouped = group_links_by_date(links)

    # Sort dates in reverse chronological order
    sorted_dates = sorted(grouped.keys(), reverse=True)

    # Format entries
    for date in sorted_dates:
        date_links = grouped[date]

        # Get episode title from first link (all links from same date share episode_title)
        episode_title = date_links[0].get('episode_title') if date_links else None

        # Date header
        header = format_date_header(
            date,
            year,
            episode_title=episode_title,
            include_episode_title=config.get('include_episode_title', False)
        )
        parts.append(header)
        parts.append(config['header_spacing'].rstrip())  # Remove trailing newlines (we'll add them consistently)

        # Links as markdown list
        for link in date_links:
            title = link['title']
            url = link['url']
            source = link['source']

            if source:
                parts.append(f"  * [{title}]({url}) ({source})")
            else:
                parts.append(f"  * [{title}]({url})")

        # Triple newline between entries
        parts.append('')
        parts.append('')
        parts.append('')

    return '\n'.join(parts)


def compute_content_hash(content):
    """Compute SHA256 hash of content string."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def should_write_file(file_path, new_content):
    """
    Check if file should be written based on content hash.

    Returns:
        bool: True if file should be written (doesn't exist or content changed)
    """
    if not os.path.exists(file_path):
        return True

    with open(file_path, 'r', encoding='utf-8') as f:
        existing_content = f.read()

    return compute_content_hash(existing_content) != compute_content_hash(new_content)


def generate_year_page(db_path, year, page_type, output_dir='docs', force=False):
    """
    Generate a single year page.

    Args:
        db_path: Path to SQLite database
        year: Year to generate
        page_type: 'showlinks' or 'longreads'
        output_dir: Output directory for markdown files
        force: If True, always write file (skip hash check)

    Returns:
        tuple: (file_path, 'written'|'skipped'|'no_data')
    """
    config = PAGE_CONFIGS[page_type]

    # Get links for this year
    links = get_links_for_year(db_path, year, config['link_type'])

    if not links:
        return (None, 'no_data')

    # Generate markdown
    content = generate_markdown_content(year, config['link_type'], links, config)

    # Determine output path
    file_path = os.path.join(output_dir, f"{config['output_prefix']}-{year}.md")

    # Check if we should write
    if not force and not should_write_file(file_path, content):
        return (file_path, 'skipped')

    # Write file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return (file_path, 'written')


def generate_all_year_pages(db_path='ridehome.db', output_dir='docs', force=False):
    """
    Generate all year pages for all types.

    Args:
        db_path: Path to SQLite database
        output_dir: Output directory
        force: If True, regenerate all files (skip hash checks)

    Returns:
        dict: Statistics about what was generated
    """
    stats = {
        'written': 0,
        'skipped': 0,
        'no_data': 0,
        'files': []
    }

    # Get available years from database
    available_years = get_available_years(db_path)

    # Generate pages for each type and year
    for page_type in ['showlinks', 'longreads']:
        if page_type == 'showlinks':
            link_type = 'showlink'
        else:
            link_type = 'longread'

        years = available_years.get(link_type, [])

        if not years:
            continue

        for year in years:
            file_path, status = generate_year_page(db_path, year, page_type, output_dir, force)

            stats[status] += 1

            if status == 'written':
                stats['files'].append(file_path)
                print(f"  ✓ {page_type} {year}: regenerated")
            elif status == 'skipped':
                print(f"  - {page_type} {year}: unchanged")
            elif status == 'no_data':
                print(f"  ⚠ {page_type} {year}: no data")

    return stats


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate year-based markdown pages from database'
    )
    parser.add_argument('--db', default='ridehome.db',
                        help='Database path (default: ridehome.db)')
    parser.add_argument('--output', default='docs',
                        help='Output directory (default: docs)')
    parser.add_argument('--force', action='store_true',
                        help='Force regeneration of all files')

    args = parser.parse_args()

    print("Generating year pages...")
    stats = generate_all_year_pages(args.db, args.output, args.force)

    print(f"\n✓ Generated {stats['written']} files, {stats['skipped']} unchanged")
    if stats['no_data'] > 0:
        print(f"  ({stats['no_data']} years with no data)")


if __name__ == '__main__':
    main()
