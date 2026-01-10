#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate index.md homepage from database.
Builds recent/archive navigation based on current year.
Only links to files that actually exist.
"""
import sqlite3
import os
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from status_generator import get_status_data, format_status_section

PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


def category_to_slug(category_name):
    """Convert category name to URL-safe slug."""
    return category_name.lower().replace('/', '-').replace(' ', '-')


def get_most_recent_episode(db_path='ridehome.db'):
    """
    Get the most recent episode with links.

    Returns:
        dict: {
            'date': 'YYYY-MM-DD',
            'episode_title': str,
            'links': [
                {'title': str, 'url': str, 'source': str, 'ai_category': str},
                ...
            ]
        } or None if no episodes found
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get most recent episode date
    cursor.execute("""
        SELECT DISTINCT episode_date, episode_title
        FROM links
        WHERE link_type = 'showlink'
          AND episode_title IS NOT NULL
        ORDER BY episode_date_unix DESC
        LIMIT 1
    """)

    result = cursor.fetchone()
    if not result:
        conn.close()
        return None

    episode_date, episode_title = result

    # Get all links for this episode
    cursor.execute("""
        SELECT title, url, source, ai_category
        FROM links
        WHERE episode_date = ?
          AND link_type = 'showlink'
        ORDER BY id
    """, (episode_date,))

    links = []
    for row in cursor.fetchall():
        links.append({
            'title': row[0],
            'url': row[1],
            'source': row[2],
            'ai_category': row[3]
        })

    conn.close()

    return {
        'date': episode_date,
        'episode_title': episode_title,
        'links': links
    }


def get_max_year_from_db(db_path='ridehome.db'):
    """
    Get the most recent year in the database.

    Returns:
        int: Most recent year with data
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT MAX(strftime('%Y', date))
        FROM links
    """)

    result = cursor.fetchone()[0]
    conn.close()

    if result:
        return int(result)

    # Fallback to current year
    return datetime.now(PACIFIC_TZ).year


def scan_existing_files(docs_dir='docs'):
    """
    Scan docs directory for existing files.

    Returns:
        dict: {
            'showlinks': [2026, 2025, ...],
            'longreads': [2025, 2024, ...],
            'wrapped': [2025, 2024, ...],
            'categories': ['ai-machine-learning', ...]
        }
    """
    docs_path = Path(docs_dir)
    existing = {
        'showlinks': [],
        'longreads': [],
        'wrapped': [],
        'categories': []
    }

    # Find showlinks files (all-links-YYYY.md)
    for file in docs_path.glob('all-links-*.md'):
        year = file.stem.replace('all-links-', '')
        if year.isdigit():
            existing['showlinks'].append(int(year))

    # Find longreads files (longreads-YYYY.md)
    for file in docs_path.glob('longreads-*.md'):
        year = file.stem.replace('longreads-', '')
        if year.isdigit():
            existing['longreads'].append(int(year))

    # Find wrapped files (YYYY-wrapped.md)
    for file in docs_path.glob('*-wrapped.md'):
        year = file.stem.replace('-wrapped', '')
        if year.isdigit():
            existing['wrapped'].append(int(year))

    # Find category files
    categories_dir = docs_path / 'categories'
    if categories_dir.exists():
        for file in categories_dir.glob('*.md'):
            existing['categories'].append(file.stem)

    # Sort years descending
    existing['showlinks'].sort(reverse=True)
    existing['longreads'].sort(reverse=True)
    existing['wrapped'].sort(reverse=True)
    existing['categories'].sort()

    return existing


def format_recent_shows_section(episode_data):
    """
    Format Recent Shows section with robot/bubble styling.

    Args:
        episode_data: dict from get_most_recent_episode()

    Returns:
        str: HTML for Recent Shows section
    """
    if not episode_data:
        return ''

    parts = []
    parts.append('<section class="recent-shows">')
    parts.append('  <h2>Most Recent Episode</h2>')

    # Format date
    date_obj = datetime.strptime(episode_data['date'], '%Y-%m-%d')
    formatted_date = date_obj.strftime('%A, %B %d, %Y')

    parts.append(f'  <h3>{formatted_date} - {episode_data["episode_title"]}</h3>')
    parts.append('  <ul>')

    for link in episode_data['links']:
        title = link['title']
        url = link['url']
        source = link['source']
        ai_category = link.get('ai_category')

        # Build link with robot/bubble if category exists
        if source and ai_category:
            category_slug = category_to_slug(ai_category)
            category_url = f"categories/{category_slug}.html"
            parts.append(f'    <li><a href="{url}">{title}</a> ({source}) &mdash; 🤖 <a href="{category_url}" class="ai-category">{ai_category}</a></li>')
        elif source:
            parts.append(f'    <li><a href="{url}">{title}</a> ({source})</li>')
        else:
            parts.append(f'    <li><a href="{url}">{title}</a></li>')

    parts.append('  </ul>')
    parts.append('</section>')
    parts.append('')

    return '\n'.join(parts)


def determine_recent_wrapped_year():
    """
    Determine which wrapped year should be in "recent" section.

    Returns:
        int or None: Year for recent wrapped, or None if none should be recent
    """
    now = datetime.now(PACIFIC_TZ)
    current_year = now.year
    current_month = now.month

    if current_month < 12:  # Jan-Nov
        return current_year - 1
    else:  # December
        return current_year


def generate_index_content(db_path='ridehome.db', docs_dir='docs'):
    """
    Generate complete index.md content.

    Returns:
        str: Complete index.md markdown content
    """
    # Get current year from database
    current_year = get_max_year_from_db(db_path)

    # Scan filesystem for existing files
    existing = scan_existing_files(docs_dir)

    # Get most recent episode
    recent_episode = get_most_recent_episode(db_path)
    recent_shows_section = format_recent_shows_section(recent_episode)

    # Get status section
    status_data = get_status_data(db_path)
    status_section = format_status_section(status_data)

    # Build index content
    parts = []

    # Header
    parts.append('')
    parts.append('[The Ride Home](https://www.ridehome.info/show/techmeme-ride-home/) now has a proper web site and [RSS feed](https://rss.art19.com/techmeme-ridehome).')
    parts.append('')

    # Recent Shows section (NEW - at top)
    if recent_shows_section:
        parts.append(recent_shows_section)

    # Recent Content section
    parts.append('<nav class="recent-nav" aria-labelledby="recent-heading">')
    parts.append('  <h2 id="recent-heading">Recent Content</h2>')
    parts.append('  <div class="nav-grid">')

    # Add current year showlinks (if exists)
    if current_year in existing['showlinks']:
        parts.append('    <a href="all-links-{}.html" class="nav-card">'.format(current_year))
        parts.append('      <h3>Show Links {}</h3>'.format(current_year))
        parts.append('      <p class="nav-description">Daily tech news links from The Ride Home podcast</p>')
        parts.append('    </a>')

    # Add most recent longreads (if exists)
    if existing['longreads']:
        recent_longreads_year = existing['longreads'][0]
        parts.append('    <a href="longreads-{}.html" class="nav-card">'.format(recent_longreads_year))
        parts.append('      <h3>Longreads {}</h3>'.format(recent_longreads_year))
        parts.append('      <p class="nav-description">Weekend reading recommendations from Friday episodes</p>')
        parts.append('    </a>')

    # Add recent wrapped (if exists)
    recent_wrapped_year = determine_recent_wrapped_year()
    if recent_wrapped_year and recent_wrapped_year in existing['wrapped']:
        parts.append('    <a href="{}-wrapped.html" class="nav-card">'.format(recent_wrapped_year))
        parts.append('      <h3>{} Wrapped</h3>'.format(recent_wrapped_year))
        parts.append('      <p class="nav-description">Year in review with top sources and topics</p>')
        parts.append('    </a>')

    parts.append('  </div>')
    parts.append('</nav>')
    parts.append('')

    # Status section (moved below Recent Content)
    parts.append('<!-- STATUS_SECTION -->')
    parts.append('')
    parts.append(status_section)
    parts.append('<!-- END_STATUS_SECTION -->')
    parts.append('')

    # Archive section
    parts.append('<nav class="archive-nav" aria-labelledby="archive-heading">')
    parts.append('  <h2 id="archive-heading">Archive</h2>')
    parts.append('  <div class="archive-grid">')

    # Show Links column
    parts.append('    <div class="archive-column">')
    parts.append('      <h3>Show Links</h3>')
    parts.append('      <ul>')
    for year in existing['showlinks']:
        if year < current_year:  # Archive = everything before current year
            parts.append('        <li><a href="all-links-{}.html">{}</a></li>'.format(year, year))
    parts.append('      </ul>')
    parts.append('    </div>')

    # Longreads column
    parts.append('    <div class="archive-column">')
    parts.append('      <h3>Longreads</h3>')
    parts.append('      <ul>')

    # Archive longreads (skip the most recent one if it's in "recent" section)
    recent_longreads_year = existing['longreads'][0] if existing['longreads'] else None
    for year in existing['longreads']:
        if year != recent_longreads_year:  # Don't duplicate recent entry
            parts.append('        <li><a href="longreads-{}.html">{}</a></li>'.format(year, year))

    # Special longreads files
    special_longreads = [
        ('longreads.html', 'Pre-2018'),
        ('coronavirus-daily-briefing.html', 'COVID-19 Archive')
    ]
    for href, label in special_longreads:
        file_path = os.path.join(docs_dir, href.replace('.html', '.md'))
        if os.path.exists(file_path):
            parts.append('        <li><a href="{}">{}</a></li>'.format(href, label))

    parts.append('      </ul>')
    parts.append('    </div>')

    # Wrapped column
    parts.append('    <div class="archive-column">')
    parts.append('      <h3>Wrapped</h3>')
    parts.append('      <ul>')

    # Archive wrapped (exclude recent wrapped year)
    for year in existing['wrapped']:
        if year != recent_wrapped_year:
            parts.append('        <li><a href="{}-wrapped.html">{}</a></li>'.format(year, year))

    parts.append('      </ul>')
    parts.append('    </div>')

    # Categories column
    parts.append('    <div class="archive-column">')
    parts.append('      <h3>Categories</h3>')
    parts.append('      <ul>')

    # Category links
    category_labels = {
        'ai-machine-learning': 'AI/Machine Learning',
        'automotive-mobility': 'Automotive/Mobility',
        'cloud-enterprise': 'Cloud/Enterprise',
        'crypto-blockchain': 'Crypto/Blockchain',
        'e-commerce-retail': 'E-commerce/Retail',
        'gaming': 'Gaming',
        'hardware-chips': 'Hardware/Chips',
        'other-tech-news': 'Other Tech News',
        'regulation-policy': 'Regulation/Policy',
        'security-privacy': 'Security/Privacy',
        'social-media': 'Social Media',
        'streaming-entertainment': 'Streaming/Entertainment'
    }

    for slug in existing['categories']:
        label = category_labels.get(slug, slug.replace('-', '/').title())
        parts.append('        <li><a href="categories/{}.html">{}</a></li>'.format(slug, label))

    parts.append('      </ul>')
    parts.append('    </div>')

    parts.append('  </div>')
    parts.append('</nav>')
    parts.append('')
    parts.append('')

    return '\n'.join(parts)


def write_index(content, output_path='docs/index.md'):
    """Write index.md file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate index.md homepage from database'
    )
    parser.add_argument('--db', default='ridehome.db',
                        help='Database path (default: ridehome.db)')
    parser.add_argument('--docs', default='docs',
                        help='Docs directory (default: docs)')
    parser.add_argument('--output', default='docs/index.md',
                        help='Output file path (default: docs/index.md)')

    args = parser.parse_args()

    print("Generating index.md...")

    content = generate_index_content(args.db, args.docs)
    write_index(content, args.output)

    print(f"✓ Generated {args.output}")


if __name__ == '__main__':
    main()
