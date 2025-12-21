#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Load markdown files into SQLite database.
One-time import script for existing markdown archives.
"""
import argparse
import sys
from pathlib import Path
from db_schema import create_schema
from markdown_parser import parse_showlinks_file, parse_longreads_file
from db_writer import insert_links


def load_showlinks(conn, docs_dir='docs'):
    """
    Load all showlinks markdown files into database.

    Args:
        conn: Database connection
        docs_dir: Directory containing markdown files

    Returns:
        Tuple of (total_inserted, total_duplicates)
    """
    docs_path = Path(docs_dir)

    # Load yearly files (2018+)
    showlinks_files = sorted(docs_path.glob('all-links-2*.md'))

    total_inserted = 0
    total_duplicates = 0

    print(f"Found {len(showlinks_files)} showlinks files to import")

    for file_path in showlinks_files:
        print(f"\nParsing {file_path.name}...", end=' ')
        entries = parse_showlinks_file(str(file_path))
        print(f"{len(entries)} links found")

        if entries:
            inserted, duplicates = insert_links(conn, entries, 'showlink')
            total_inserted += inserted
            total_duplicates += duplicates
            print(f"  Inserted: {inserted}, Duplicates: {duplicates}")

    return (total_inserted, total_duplicates)


def load_longreads(conn, docs_dir='docs'):
    """
    Load all longreads markdown files into database.

    Args:
        conn: Database connection
        docs_dir: Directory containing markdown files

    Returns:
        Tuple of (total_inserted, total_duplicates)
    """
    docs_path = Path(docs_dir)
    longreads_files = sorted(docs_path.glob('longreads-*.md'))

    total_inserted = 0
    total_duplicates = 0

    print(f"Found {len(longreads_files)} longreads files to import")

    for file_path in longreads_files:
        print(f"\nParsing {file_path.name}...", end=' ')
        entries = parse_longreads_file(str(file_path))
        print(f"{len(entries)} links found")

        if entries:
            inserted, duplicates = insert_links(conn, entries, 'longread')
            total_inserted += inserted
            total_duplicates += duplicates
            print(f"  Inserted: {inserted}, Duplicates: {duplicates}")

    return (total_inserted, total_duplicates)


def main():
    parser = argparse.ArgumentParser(description='Load markdown files into SQLite database')
    parser.add_argument('--type', choices=['showlinks', 'longreads', 'all'], default='all',
                        help='Type of links to import (default: all)')
    parser.add_argument('--db', default='ridehome.db',
                        help='Database file path (default: ridehome.db)')
    parser.add_argument('--docs-dir', default='docs',
                        help='Directory containing markdown files (default: docs)')

    args = parser.parse_args()

    # Create database schema
    print(f"Creating/opening database: {args.db}")
    conn = create_schema(args.db)

    # Import based on type
    if args.type in ['showlinks', 'all']:
        print("\n" + "="*60)
        print("IMPORTING SHOWLINKS")
        print("="*60)
        inserted, duplicates = load_showlinks(conn, args.docs_dir)
        print(f"\n✓ Total showlinks imported: {inserted}")
        if duplicates > 0:
            print(f"  ({duplicates} duplicates skipped)")

    if args.type in ['longreads', 'all']:
        print("\n" + "="*60)
        print("IMPORTING LONGREADS")
        print("="*60)
        inserted, duplicates = load_longreads(conn, args.docs_dir)
        print(f"\n✓ Total longreads imported: {inserted}")
        if duplicates > 0:
            print(f"  ({duplicates} duplicates skipped)")

    # Show summary
    print("\n" + "="*60)
    print("DATABASE SUMMARY")
    print("="*60)

    cursor = conn.cursor()
    cursor.execute("SELECT link_type, COUNT(*) FROM links GROUP BY link_type")
    for link_type, count in cursor.fetchall():
        print(f"  {link_type}: {count}")

    cursor.execute("SELECT COUNT(*) FROM links")
    total = cursor.fetchone()[0]
    print(f"  TOTAL: {total}")

    conn.close()
    print(f"\n✓ Database saved to {args.db}")


if __name__ == '__main__':
    main()
