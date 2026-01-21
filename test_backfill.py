#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for AI categorization backfill functionality.

Run with:
    python3 test_backfill.py
"""
import unittest
import sqlite3
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
from db_schema import create_schema
from backfill_ai_categories import (
    get_uncategorized_links,
    save_categorizations,
    estimate_cost,
    backfill_categories
)


class TestDatabaseSchema(unittest.TestCase):
    """Test that base database schema includes AI categorization columns"""

    def setUp(self):
        """Create temporary database for testing"""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')

    def tearDown(self):
        """Remove temporary database"""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_base_schema_includes_ai_columns(self):
        """Test that create_schema includes AI categorization columns"""
        # Create database with base schema
        conn = create_schema(self.db_path)

        # Verify columns exist
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(links)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        self.assertIn('ai_category', columns)
        self.assertIn('ai_categorized_at', columns)
        self.assertIn('ai_model', columns)

    def test_base_schema_includes_ai_indexes(self):
        """Test that create_schema includes AI categorization indexes"""
        # Create database with base schema
        conn = create_schema(self.db_path)

        # Verify indexes exist
        cursor = conn.cursor()
        cursor.execute("PRAGMA index_list(links)")
        indexes = {row[1] for row in cursor.fetchall()}
        conn.close()

        self.assertIn('idx_links_ai_category', indexes)
        self.assertIn('idx_links_ai_categorized_at', indexes)


class TestUncategorizedLinks(unittest.TestCase):
    """Test finding uncategorized links"""

    def setUp(self):
        """Create test database with sample data"""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create table with AI columns
        cursor.execute("""
            CREATE TABLE links (
                id INTEGER PRIMARY KEY,
                title TEXT,
                url TEXT,
                date_unix INTEGER,
                ai_category TEXT,
                ai_categorized_at TIMESTAMP,
                ai_model TEXT
            )
        """)

        # Insert test data
        test_data = [
            (1, 'OpenAI Releases GPT-5', 'http://example.com/1', 1700000000, None, None, None),
            (2, 'Tesla Announces New Model', 'http://example.com/2', 1700000001, 'Automotive/Mobility', '2025-01-01', 'haiku'),
            (3, 'Apple Launches New iPhone', 'http://example.com/3', 1700000002, None, None, None),
            (4, None, 'http://example.com/4', 1700000003, None, None, None),  # No title
            (5, '', 'http://example.com/5', 1700000004, None, None, None),  # Empty title
        ]

        cursor.executemany("""
            INSERT INTO links (id, title, url, date_unix, ai_category, ai_categorized_at, ai_model)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, test_data)

        conn.commit()
        conn.close()

    def tearDown(self):
        """Remove test database"""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_get_uncategorized_links(self):
        """Test retrieving uncategorized links"""
        links = get_uncategorized_links(self.db_path)

        # Should return 2 links (IDs 1 and 3)
        # Should NOT return: ID 2 (categorized), ID 4 (no title), ID 5 (empty title)
        self.assertEqual(len(links), 2)

        ids = [link[0] for link in links]
        self.assertIn(1, ids)
        self.assertIn(3, ids)
        self.assertNotIn(2, ids)
        self.assertNotIn(4, ids)
        self.assertNotIn(5, ids)

    def test_get_uncategorized_links_with_limit(self):
        """Test limit parameter"""
        links = get_uncategorized_links(self.db_path, limit=1)
        self.assertEqual(len(links), 1)

    def test_get_uncategorized_links_all_categorized(self):
        """Test when all links are already categorized"""
        # Update all links to be categorized
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE links
            SET ai_category = 'Test Category',
                ai_categorized_at = CURRENT_TIMESTAMP
            WHERE title IS NOT NULL AND title != ''
        """)
        conn.commit()
        conn.close()

        links = get_uncategorized_links(self.db_path)
        self.assertEqual(len(links), 0)


class TestSaveCategorizations(unittest.TestCase):
    """Test saving categorizations to database"""

    def setUp(self):
        """Create test database"""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE links (
                id INTEGER PRIMARY KEY,
                title TEXT,
                ai_category TEXT,
                ai_categorized_at TIMESTAMP,
                ai_model TEXT
            )
        """)

        cursor.executemany("""
            INSERT INTO links (id, title) VALUES (?, ?)
        """, [(1, 'Title 1'), (2, 'Title 2'), (3, 'Title 3')])

        conn.commit()
        conn.close()

    def tearDown(self):
        """Remove test database"""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_save_categorizations(self):
        """Test saving categorizations"""
        categorizations = {
            1: 'AI/Machine Learning',
            2: 'Hardware/Chips',
            3: 'Other Tech News'
        }

        updated = save_categorizations(
            self.db_path,
            categorizations,
            'claude-haiku-4-5-20251001'
        )

        self.assertEqual(updated, 3)

        # Verify data was saved correctly
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, ai_category, ai_model
            FROM links
            ORDER BY id
        """)
        results = cursor.fetchall()
        conn.close()

        self.assertEqual(results[0][1], 'AI/Machine Learning')
        self.assertEqual(results[1][1], 'Hardware/Chips')
        self.assertEqual(results[2][1], 'Other Tech News')

        # All should have the same model
        for row in results:
            self.assertEqual(row[2], 'claude-haiku-4-5-20251001')

    def test_save_empty_categorizations(self):
        """Test saving empty categorizations dict"""
        updated = save_categorizations(self.db_path, {}, 'test-model')
        self.assertEqual(updated, 0)


class TestCostEstimation(unittest.TestCase):
    """Test cost estimation"""

    def test_estimate_cost_haiku_100_titles(self):
        """Test cost estimate for 100 titles with Haiku"""
        cost = estimate_cost(100, 'haiku')
        # Should be around $0.01
        self.assertGreater(cost, 0.0)
        self.assertLess(cost, 0.02)

    def test_estimate_cost_haiku_10000_titles(self):
        """Test cost estimate for 10,000 titles with Haiku"""
        cost = estimate_cost(10000, 'haiku')
        # Should be around $0.60-$1.50
        self.assertGreater(cost, 0.5)
        self.assertLess(cost, 2.0)

    def test_estimate_cost_sonnet_more_expensive(self):
        """Test that Sonnet costs more than Haiku"""
        cost_haiku = estimate_cost(1000, 'haiku')
        cost_sonnet = estimate_cost(1000, 'sonnet')

        # Sonnet should be about 3x more expensive
        self.assertGreater(cost_sonnet, cost_haiku * 2.5)
        self.assertLess(cost_sonnet, cost_haiku * 3.5)


class TestBackfillIntegration(unittest.TestCase):
    """Integration tests for backfill process"""

    def setUp(self):
        """Create test database with uncategorized links"""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE links (
                id INTEGER PRIMARY KEY,
                title TEXT,
                url TEXT,
                date_unix INTEGER,
                ai_category TEXT,
                ai_categorized_at TIMESTAMP,
                ai_model TEXT
            )
        """)

        # Insert test links
        test_links = [
            (1, 'OpenAI Launches GPT-5', 'http://example.com/1', 1700000000),
            (2, 'Tesla Model 3 Sales Surge', 'http://example.com/2', 1700000001),
            (3, 'Apple Vision Pro Released', 'http://example.com/3', 1700000002),
        ]

        cursor.executemany("""
            INSERT INTO links (id, title, url, date_unix)
            VALUES (?, ?, ?, ?)
        """, test_links)

        conn.commit()
        conn.close()

    def tearDown(self):
        """Remove test database"""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_dry_run(self):
        """Test dry run mode"""
        result = backfill_categories(
            batch_size=100,
            limit=10,
            dry_run=True,
            db_path=self.db_path
        )

        self.assertIsNotNone(result)
        self.assertEqual(result['total'], 3)
        self.assertEqual(result['processed'], 0)
        self.assertEqual(result['cost'], 0.0)

        # Verify nothing was saved
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM links WHERE ai_category IS NOT NULL")
        count = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(count, 0)

    @patch('backfill_ai_categories.categorize_with_retry')
    @patch('builtins.input', return_value='y')
    def test_backfill_with_mocked_api(self, mock_input, mock_categorize):
        """Test backfill with mocked Claude API"""
        # Mock the API response
        mock_categorize.return_value = {
            'OpenAI Launches GPT-5': 'AI/Machine Learning',
            'Tesla Model 3 Sales Surge': 'Automotive/Mobility',
            'Apple Vision Pro Released': 'Hardware/Chips'
        }

        # Set fake API key
        os.environ['ANTHROPIC_API_KEY'] = 'test-key'

        try:
            result = backfill_categories(
                batch_size=100,
                limit=10,
                dry_run=False,
                db_path=self.db_path
            )

            self.assertIsNotNone(result)
            self.assertEqual(result['total'], 3)
            self.assertEqual(result['processed'], 3)

            # Verify data was saved
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ai_category
                FROM links
                ORDER BY id
            """)
            results = cursor.fetchall()
            conn.close()

            self.assertEqual(results[0][1], 'AI/Machine Learning')
            self.assertEqual(results[1][1], 'Automotive/Mobility')
            self.assertEqual(results[2][1], 'Hardware/Chips')

        finally:
            # Clean up
            if 'ANTHROPIC_API_KEY' in os.environ:
                del os.environ['ANTHROPIC_API_KEY']


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseSchema))
    suite.addTests(loader.loadTestsFromTestCase(TestUncategorizedLinks))
    suite.addTests(loader.loadTestsFromTestCase(TestSaveCategorizations))
    suite.addTests(loader.loadTestsFromTestCase(TestCostEstimation))
    suite.addTests(loader.loadTestsFromTestCase(TestBackfillIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
