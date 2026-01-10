#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database writer for The Ride Home links.
Handles insertion with duplicate detection and date conversion.
"""
import sqlite3
from datetime import datetime
from typing import List, Dict
import time


def date_to_unix(date_obj: datetime) -> int:
    """
    Convert datetime object to Unix timestamp.

    Args:
        date_obj: datetime object

    Returns:
        Unix timestamp as integer
    """
    return int(date_obj.timestamp())


def insert_links(conn: sqlite3.Connection, entries: List[Dict], link_type: str) -> tuple:
    """
    Insert links into database with duplicate detection.

    Args:
        conn: Database connection
        entries: List of dicts with keys: date, title, url, source, episode_date, episode_title
        link_type: Either 'showlink' or 'longread'

    Returns:
        Tuple of (inserted_count, duplicate_count)
    """
    cursor = conn.cursor()
    inserted = 0
    duplicates = 0

    for entry in entries:
        # Convert datetime to ISO format and Unix timestamp
        date_iso = entry['date'].strftime('%Y-%m-%d')
        date_unix = date_to_unix(entry['date'])

        episode_date_iso = entry['episode_date'].strftime('%Y-%m-%d')
        episode_date_unix = date_to_unix(entry['episode_date'])

        try:
            cursor.execute('''
                INSERT INTO links (date, date_unix, title, url, source, link_type, episode_date, episode_date_unix, episode_title)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                date_iso,
                date_unix,
                entry['title'],
                entry['url'],
                entry['source'],
                link_type,
                episode_date_iso,
                episode_date_unix,
                entry.get('episode_title')
            ))
            inserted += 1
        except sqlite3.IntegrityError:
            # Duplicate URL + date combination
            duplicates += 1

    conn.commit()
    return (inserted, duplicates)


if __name__ == '__main__':
    # Test with sample data
    from db_schema import create_schema

    # Create test database
    conn = create_schema(':memory:')

    # Sample entries
    test_entries = [
        {
            'date': datetime(2025, 12, 12),
            'title': 'Test Article',
            'url': 'https://example.com/test',
            'source': 'Example',
            'episode_date': datetime(2025, 12, 12),
            'episode_title': 'Test Episode'
        }
    ]

    inserted, dupes = insert_links(conn, test_entries, 'showlink')
    print(f"Inserted: {inserted}, Duplicates: {dupes}")

    # Verify insertion
    cursor = conn.cursor()
    cursor.execute('SELECT date, date_unix, title, url, source FROM links')
    for row in cursor.fetchall():
        print(f"  {row}")

    # Test duplicate detection
    inserted, dupes = insert_links(conn, test_entries, 'showlink')
    print(f"\nSecond insert - Inserted: {inserted}, Duplicates: {dupes}")

    conn.close()
