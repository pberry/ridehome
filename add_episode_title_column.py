#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Add episode_title column and backfill from RSS feed.

This script:
1. Adds episode_title column to existing databases (if needed)
2. Fetches RSS feed to extract episode titles
3. Updates all links with their episode titles based on episode_date

Usage:
    # Dry run (show what would be done)
    python3 add_episode_title_column.py --dry-run

    # Run migration and backfill
    python3 add_episode_title_column.py
"""
import os
import sqlite3
import argparse
import feedparser
import time
from datetime import datetime
from zoneinfo import ZoneInfo

PACIFIC_TZ = ZoneInfo("America/Los_Angeles")
RSS_FEED_URL = "https://feeds.megaphone.fm/ridehome"


def add_column_if_needed(db_path='ridehome.db', dry_run=False):
    """
    Add episode_title column to links table if it doesn't exist.

    Args:
        db_path: Path to database
        dry_run: If True, only print what would be done

    Returns:
        bool: True if column was added, False if it already existed
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(links)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'episode_title' in columns:
        print("✓ episode_title column already exists")
        conn.close()
        return False

    if dry_run:
        print("[DRY RUN] Would add episode_title column to links table")
        conn.close()
        return True

    # Add the column
    print("Adding episode_title column...")
    cursor.execute("ALTER TABLE links ADD COLUMN episode_title TEXT")

    # Add index
    print("Creating index on episode_title...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_episode_title ON links(episode_title)")

    conn.commit()
    conn.close()
    print("✓ Column and index added successfully")
    return True


def fetch_episode_titles_from_rss():
    """
    Fetch RSS feed and extract episode titles with their dates.

    Returns:
        dict: Mapping of episode_date (date string) to episode title
    """
    print(f"Fetching RSS feed from {RSS_FEED_URL}...")
    feed = feedparser.parse(RSS_FEED_URL)

    episode_map = {}

    for post in feed.entries:
        # Extract episode title from post.title format: "The Ride Home - [Episode Title]"
        post_title_array = post.title.split(' - ')
        if len(post_title_array) > 1:
            episode_title = post_title_array[1]
        else:
            episode_title = post_title_array[0]

        # Convert UTC time from feed to Pacific time
        entry_time = time.struct_time(post.published_parsed)
        entry_dt_utc = datetime(*entry_time[:6], tzinfo=ZoneInfo("UTC"))
        episode_date = entry_dt_utc.astimezone(PACIFIC_TZ).replace(tzinfo=None)

        # Use date-only string as key (YYYY-MM-DD)
        episode_date_str = episode_date.strftime('%Y-%m-%d')

        episode_map[episode_date_str] = episode_title

    print(f"✓ Fetched {len(episode_map)} episodes from RSS feed")
    return episode_map


def get_links_without_episode_title(db_path='ridehome.db'):
    """
    Get all links that don't have episode_title set.

    Returns:
        list of tuples: (id, episode_date)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, episode_date
        FROM links
        WHERE episode_title IS NULL
        ORDER BY episode_date DESC
    """)

    results = cursor.fetchall()
    conn.close()

    return results


def backfill_episode_titles(db_path='ridehome.db', episode_map=None, dry_run=False, column_exists=True):
    """
    Update all links with episode titles from the episode map.

    Args:
        db_path: Path to database
        episode_map: Dict mapping episode_date to episode_title
        dry_run: If True, only print what would be done
        column_exists: If False, skip querying (for dry-run when column doesn't exist yet)

    Returns:
        tuple: (updated_count, not_found_count)
    """
    if episode_map is None:
        episode_map = fetch_episode_titles_from_rss()

    if not column_exists:
        # Column doesn't exist yet, estimate from total links
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM links")
        total_links = cursor.fetchone()[0]
        conn.close()

        print(f"\n[ESTIMATE] Would update approximately {total_links} links")
        print(f"[DRY RUN] Showing sample episode titles:")
        for i, (episode_date, episode_title) in enumerate(list(episode_map.items())[:5]):
            print(f"  Episode {episode_date}: '{episode_title}'")
        return (0, 0)

    links = get_links_without_episode_title(db_path)

    if not links:
        print("✓ All links already have episode titles")
        return (0, 0)

    print(f"\nFound {len(links)} links without episode titles")

    if dry_run:
        print(f"[DRY RUN] Would update {len(links)} links")
        # Show a sample
        sample_links = links[:5]
        print("\nSample updates (first 5):")
        for link_id, episode_date in sample_links:
            episode_title = episode_map.get(episode_date, "NOT FOUND IN RSS")
            print(f"  Link ID {link_id}, Episode {episode_date}: '{episode_title}'")
        return (0, 0)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    updated = 0
    not_found = 0

    for link_id, episode_date in links:
        episode_title = episode_map.get(episode_date)

        if episode_title:
            cursor.execute("""
                UPDATE links
                SET episode_title = ?
                WHERE id = ?
            """, (episode_title, link_id))
            updated += cursor.rowcount
        else:
            not_found += 1

    conn.commit()
    conn.close()

    return (updated, not_found)


def main():
    parser = argparse.ArgumentParser(
        description='Add episode_title column and backfill from RSS feed'
    )
    parser.add_argument('--db', default='ridehome.db',
                        help='Database path (default: ridehome.db)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without making changes')

    args = parser.parse_args()

    print("Episode Title Migration & Backfill")
    print("=" * 50)

    if args.dry_run:
        print("[DRY RUN MODE - No changes will be made]")
        print()

    # Check if database exists
    if not os.path.exists(args.db):
        print(f"Error: Database not found at {args.db}")
        return 1

    # Step 1: Add column if needed
    print("\n1. Checking database schema...")
    column_added = add_column_if_needed(args.db, args.dry_run)

    # Step 2: Fetch episode titles from RSS
    print("\n2. Fetching episode titles from RSS feed...")
    episode_map = fetch_episode_titles_from_rss()

    # Step 3: Backfill existing links
    print("\n3. Backfilling episode titles...")
    # In dry-run mode, if column needs to be added, it doesn't exist yet
    column_exists = not (args.dry_run and column_added)
    updated, not_found = backfill_episode_titles(args.db, episode_map, args.dry_run, column_exists)

    # Summary
    print("\n" + "=" * 50)
    print("Summary:")
    if column_added:
        print("  ✓ Added episode_title column")
    print(f"  ✓ Fetched {len(episode_map)} episodes from RSS")

    if not args.dry_run:
        print(f"  ✓ Updated {updated} links with episode titles")
        if not_found > 0:
            print(f"  ⚠ {not_found} links not found in RSS feed (older episodes)")
    else:
        print("  [DRY RUN] No changes made to database")

    print("\nNext steps:")
    if args.dry_run:
        print("  1. Run without --dry-run to apply changes")
    else:
        print("  1. Regenerate markdown: python3 generate_year_pages.py --force")
        print("  2. Verify output: head -20 docs/all-links-2026.md")

    return 0


if __name__ == '__main__':
    exit(main())
