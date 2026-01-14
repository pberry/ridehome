#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate category pages from AI-categorized links in database.
"""
import sqlite3
from datetime import datetime


MONTH_NAMES = [
    '', 'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]


def category_to_slug(category_name):
    """Convert category name to URL-safe slug."""
    return category_name.lower().replace('/', '-').replace(' ', '-')


def get_links_for_category(db_path, category_name):
    """
    Query database for links in a category, grouped by year and month.

    Returns:
        dict: {year: {month: [links]}} with years and months in descending order
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute('''
            SELECT date, title, url, source
            FROM links
            WHERE ai_category = ?
            ORDER BY date_unix DESC
        ''', (category_name,))

        rows = cursor.fetchall()

    result = {}
    for row in rows:
        date_str, title, url, source = row
        date = datetime.strptime(date_str, '%Y-%m-%d')
        year = date.year
        month = date.month

        if year not in result:
            result[year] = {}
        if month not in result[year]:
            result[year][month] = []

        result[year][month].append({
            'date': date_str,
            'title': title,
            'url': url,
            'source': source
        })

    return result


def generate_category_markdown(grouped_links, category_name):
    """
    Generate markdown content for a category page.

    Args:
        grouped_links: dict {year: {month: [links]}}
        category_name: str category name for the page title

    Returns:
        str: Complete markdown content with front matter
    """
    lines = []

    # Jekyll front matter
    lines.append('---')
    lines.append(f'title: {category_name}')
    lines.append('layout: category')
    lines.append('---')
    lines.append('')

    # Include header
    lines.append('{% include categories/header.md %}')
    lines.append('')

    # Years in descending order
    for year in sorted(grouped_links.keys(), reverse=True):
        lines.append(f'## {year}')
        lines.append('')

        # Months in descending order
        for month in sorted(grouped_links[year].keys(), reverse=True):
            month_name = MONTH_NAMES[month]
            lines.append(f'### {month_name}')
            lines.append('')

            # Links within month (already sorted by date descending from DB query)
            for link in grouped_links[year][month]:
                if link['source']:
                    lines.append(f"- [{link['title']}]({link['url']}) ({link['source']})")
                else:
                    lines.append(f"- [{link['title']}]({link['url']})")

            lines.append('')

    return '\n'.join(lines)


def get_all_categories(db_path):
    """Get list of all categories that have links."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT ai_category
            FROM links
            WHERE ai_category IS NOT NULL
            ORDER BY ai_category
        ''')
        return [row[0] for row in cursor.fetchall()]


def generate_sidebar(categories, sidebar_path='docs/_includes/categories/sidebar.html'):
    """
    Generate category sidebar HTML.

    Args:
        categories: List of category names (sorted)
        sidebar_path: Output path for sidebar HTML
    """
    lines = []
    lines.append('<aside class="category-sidebar">')
    lines.append('  <h2>Categories</h2>')
    lines.append('  <ul>')

    for category in categories:
        slug = category_to_slug(category)
        lines.append(f'    <li><a href="/ridehome/categories/{slug}.html">{category}</a></li>')

    lines.append('  </ul>')
    lines.append('</aside>')

    sidebar_html = '\n'.join(lines) + '\n'

    with open(sidebar_path, 'w', encoding='utf-8') as f:
        f.write(sidebar_html)

    return sidebar_html


def generate_all_category_pages(db_path='ridehome.db', output_dir='docs/categories'):
    """Generate category pages for all categories in database."""
    import os

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Get all categories
    categories = get_all_categories(db_path)

    if not categories:
        print("No categories found in database")
        return

    print(f"Generating category pages for {len(categories)} categories...")

    for category in categories:
        # Get links for this category
        grouped_links = get_links_for_category(db_path, category)

        if not grouped_links:
            print(f"  ⚠ Skipping {category} (no links)")
            continue

        # Generate markdown
        markdown = generate_category_markdown(grouped_links, category)

        # Write to file
        slug = category_to_slug(category)
        file_path = os.path.join(output_dir, f'{slug}.md')

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        # Count total links
        total_links = sum(len(links) for year_data in grouped_links.values() for links in year_data.values())
        print(f"  ✓ {category}: {total_links} links → {file_path}")

    # Generate sidebar (no link counts, only regenerates when categories change)
    print("\nGenerating category sidebar...")
    generate_sidebar(categories)
    print("  ✓ Sidebar generated at docs/_includes/categories/sidebar.html")

    print(f"\n✓ Generated {len(categories)} category pages in {output_dir}/")


if __name__ == '__main__':
    generate_all_category_pages()
