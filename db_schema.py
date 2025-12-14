#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database schema for The Ride Home links database.
"""
import sqlite3
from pathlib import Path


def create_schema(db_path='ridehome.db'):
    """
    Create the links database schema.

    Args:
        db_path: Path to SQLite database file

    Returns:
        sqlite3.Connection: Database connection with schema created
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create links table with hybrid date storage
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            date_unix INTEGER NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            source TEXT,
            link_type TEXT NOT NULL CHECK(link_type IN ('showlink', 'longread')),
            episode_date TEXT NOT NULL,
            episode_date_unix INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create indexes for common queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON links(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date_unix ON links(date_unix)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_link_type ON links(link_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON links(source)')

    # Create unique constraint to prevent duplicates (URL + date)
    cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_url_date
        ON links(url, date)
    ''')

    conn.commit()
    return conn


if __name__ == '__main__':
    # Create schema for testing
    conn = create_schema()
    print("Schema created successfully")

    # Show table info
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(links)")
    print("\nTable schema:")
    for row in cursor.fetchall():
        print(f"  {row}")

    cursor.execute("PRAGMA index_list(links)")
    print("\nIndexes:")
    for row in cursor.fetchall():
        print(f"  {row}")

    conn.close()
