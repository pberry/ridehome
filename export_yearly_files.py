#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export yearly markdown files from SQLite database.
Generates all-links-YYYY.md and longreads-YYYY.md for each year in the database.
"""
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime


def export_showlinks_by_year(conn, output_dir='docs'):
    """
    Export showlinks grouped by year to separate markdown files.

    Args:
        conn: Database connection
        output_dir: Directory to write files
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    cursor = conn.cursor()

    # Get all years with showlinks
    cursor.execute("""
        SELECT DISTINCT strftime('%Y', date) as year
        FROM links
        WHERE link_type = 'showlink'
        ORDER BY year
    """)

    years = [row[0] for row in cursor.fetchall()]
    print(f"Found showlinks in {len(years)} years: {', '.join(years)}")

    for year in years:
        filename = output_path / f"all-links-{year}.md"
        print(f"\nGenerating {filename.name}...", end=' ')

        # Query links for this year
        cursor.execute("""
            SELECT date, episode_date, title, url, source
            FROM links
            WHERE link_type = 'showlink'
              AND strftime('%Y', date) = ?
            ORDER BY date DESC
        """, (year,))

        rows = cursor.fetchall()
        print(f"{len(rows)} links")

        if not rows:
            continue

        # Generate markdown
        with open(filename, 'w') as f:
            # Write header
            f.write("{% include_relative _includes/showlinks-header.md %}\n\n")
            f.write("_This collection is no longe being updated. [The Ride Home](https://www.ridehome.info/podcast/techmeme-ride-home/) now has a proper web site and [RSS feed](https://feedly.com/i/subscription/feed/https://www.ridehome.info/rss/)._\n\n\n")

            current_date = None
            for date_str, episode_date_str, title, url, source in rows:
                # Parse dates
                date = datetime.strptime(date_str, '%Y-%m-%d')
                episode_date = datetime.strptime(episode_date_str, '%Y-%m-%d')

                # Write date header if changed
                if date_str != current_date:
                    current_date = date_str
                    day_name = date.strftime('%A')
                    month_day_year = date.strftime('%B %d %Y')
                    short_date = episode_date.strftime('%a. %-m/%-d')

                    f.write(f"\n**{day_name}, {month_day_year} - {short_date}**\n\n")

                # Write link
                source_str = f" ({source})" if source else ""
                f.write(f"  * [{title}]({url}){source_str}\n")


def export_longreads_by_year(conn, output_dir='docs'):
    """
    Export longreads grouped by year to separate markdown files.

    Args:
        conn: Database connection
        output_dir: Directory to write files
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    cursor = conn.cursor()

    # Get all years with longreads
    cursor.execute("""
        SELECT DISTINCT strftime('%Y', date) as year
        FROM links
        WHERE link_type = 'longread'
        ORDER BY year
    """)

    years = [row[0] for row in cursor.fetchall()]
    print(f"Found longreads in {len(years)} years: {', '.join(years)}")

    for year in years:
        filename = output_path / f"longreads-{year}.md"
        print(f"\nGenerating {filename.name}...", end=' ')

        # Query links for this year
        cursor.execute("""
            SELECT date, title, url, source
            FROM links
            WHERE link_type = 'longread'
              AND strftime('%Y', date) = ?
            ORDER BY date DESC
        """, (year,))

        rows = cursor.fetchall()
        print(f"{len(rows)} links")

        if not rows:
            continue

        # Generate markdown
        with open(filename, 'w') as f:
            # Write header
            f.write("{% include_relative _includes/longreads-header.md %}\n")
            f.write("_This collection is no longer being updated regularly. I still update it from time to time because this is the entire Long Read archive and I don't think everything transitioned to the site. [The Ride Home](https://www.ridehome.info/podcast/techmeme-ride-home/) now has a proper web site and [RSS feed](https://feedly.com/i/subscription/feed/https://www.ridehome.info/rss/)._\n\n")

            current_date = None
            for date_str, title, url, source in rows:
                # Parse date
                date = datetime.strptime(date_str, '%Y-%m-%d')

                # Write date header if changed
                if date_str != current_date:
                    current_date = date_str
                    formatted_date = date.strftime('%B %d, %Y')
                    f.write(f"\n## {formatted_date}\n\n")

                # Write link
                f.write(f"- [{title}]({url})\n")


def main():
    parser = argparse.ArgumentParser(description='Export yearly markdown files from database')
    parser.add_argument('--db', default='ridehome.db',
                        help='Database file path (default: ridehome.db)')
    parser.add_argument('--output-dir', default='docs',
                        help='Output directory (default: docs)')
    parser.add_argument('--type', choices=['showlinks', 'longreads', 'all'], default='all',
                        help='Type of files to export (default: all)')

    args = parser.parse_args()

    # Connect to database
    print(f"Opening database: {args.db}")
    conn = sqlite3.connect(args.db)

    try:
        if args.type in ['showlinks', 'all']:
            print("\n" + "="*60)
            print("EXPORTING SHOWLINKS BY YEAR")
            print("="*60)
            export_showlinks_by_year(conn, args.output_dir)

        if args.type in ['longreads', 'all']:
            print("\n" + "="*60)
            print("EXPORTING LONGREADS BY YEAR")
            print("="*60)
            export_longreads_by_year(conn, args.output_dir)

        print("\n✓ Export complete!")

    finally:
        conn.close()


if __name__ == '__main__':
    main()
