#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for status_generator.py
"""
import unittest
import tempfile
import sqlite3
from datetime import datetime, timedelta
from status_generator import (
    categorize_topic,
    get_status_data,
    format_status_section,
    update_homepage
)


class TestTopicCategorization(unittest.TestCase):
    """Test topic categorization based on title keywords"""

    def test_ai_topics(self):
        """AI/ML keywords should categorize as AI/Machine Learning"""
        test_cases = [
            "ChatGPT will now let you pick how nice it is",
            "OpenAI announces new GPT-5 model",
            "Google's Gemini AI assistant gets major update",
            "Meta develops new machine learning framework",
            "Anthropic releases Claude 3.5",
        ]
        for title in test_cases:
            with self.subTest(title=title):
                self.assertEqual(
                    categorize_topic(title),
                    'AI/Machine Learning'
                )

    def test_crypto_topics(self):
        """Crypto keywords should categorize as Crypto/Blockchain"""
        test_cases = [
            "Bitcoin reaches new all-time high",
            "Ethereum upgrade improves transaction speed",
            "NFT marketplace sees record sales",
            "Coinbase announces new features",
        ]
        for title in test_cases:
            with self.subTest(title=title):
                self.assertEqual(
                    categorize_topic(title),
                    'Crypto/Blockchain'
                )

    def test_gaming_topics(self):
        """Gaming keywords should categorize as Gaming"""
        test_cases = [
            "Riot Has a Secret Plan to Remake Its League of Legends Game",
            "Xbox Game Pass adds 15 new titles",
            "PlayStation 6 rumored for 2026 release",
            "Steam breaks concurrent user record",
        ]
        for title in test_cases:
            with self.subTest(title=title):
                self.assertEqual(
                    categorize_topic(title),
                    'Gaming'
                )

    def test_hardware_topics(self):
        """Hardware keywords should categorize as Hardware/Chips"""
        test_cases = [
            "Why Nvidia maintains its moat and Gemini won't kill OpenAI",
            "TPU Mania",
            "AMD announces new processor lineup",
            "Intel faces semiconductor shortage",
        ]
        for title in test_cases:
            with self.subTest(title=title):
                self.assertEqual(
                    categorize_topic(title),
                    'Hardware/Chips'
                )

    def test_streaming_topics(self):
        """Streaming keywords should categorize as Streaming/Entertainment"""
        test_cases = [
            "Spotify Music Library Scraped by Pirate Activist Group",
            "Netflix raises prices again",
            "YouTube announces new creator tools",
            "Disney+ adds password sharing restrictions",
        ]
        for title in test_cases:
            with self.subTest(title=title):
                self.assertEqual(
                    categorize_topic(title),
                    'Streaming/Entertainment'
                )

    def test_ecommerce_topics(self):
        """E-commerce keywords should categorize as E-commerce/Retail"""
        test_cases = [
            "Instacart Scraps All Price Tests After Customer Pushback",
            "Amazon announces Prime Day dates",
            "Shopify introduces new payment features",
            "Walmart expands grocery delivery",
        ]
        for title in test_cases:
            with self.subTest(title=title):
                self.assertEqual(
                    categorize_topic(title),
                    'E-commerce/Retail'
                )

    def test_automotive_topics(self):
        """Automotive keywords should categorize as Automotive/Mobility"""
        test_cases = [
            "Waymo resumes robotaxi service in San Francisco",
            "Tesla announces new Model Y features",
            "Uber expands autonomous vehicle testing",
            "Rivian delivers 10,000th electric vehicle",
        ]
        for title in test_cases:
            with self.subTest(title=title):
                self.assertEqual(
                    categorize_topic(title),
                    'Automotive/Mobility'
                )

    def test_regulation_topics(self):
        """Regulation keywords should categorize as Regulation/Policy"""
        test_cases = [
            "FTC files antitrust lawsuit against tech giant",
            "Congress passes new data privacy bill",
            "SEC investigates crypto exchange",
            "DOJ approves merger with conditions",
        ]
        for title in test_cases:
            with self.subTest(title=title):
                self.assertEqual(
                    categorize_topic(title),
                    'Regulation/Policy'
                )

    def test_mixed_topics(self):
        """Titles with multiple keywords should match most specific category first"""
        # Has both "ai" and "google" - should match AI since it's about AI
        self.assertEqual(
            categorize_topic("Google Search gets AI-powered results"),
            'AI/Machine Learning'
        )

        # Has both "machine learning" and "meta" - should match AI
        self.assertEqual(
            categorize_topic("Meta announces new machine learning framework"),
            'AI/Machine Learning'
        )

    def test_uncategorized_topics(self):
        """Generic tech news should categorize as Other Tech News"""
        test_cases = [
            "Tech startup raises $50M Series B",
            "New software update fixes critical bugs",
            "Industry conference announces keynote speakers",
        ]
        for title in test_cases:
            with self.subTest(title=title):
                self.assertEqual(
                    categorize_topic(title),
                    'Other Tech News'
                )

    def test_none_title(self):
        """None title should return Other Tech News"""
        self.assertEqual(categorize_topic(None), 'Other Tech News')

    def test_empty_title(self):
        """Empty title should return Other Tech News"""
        self.assertEqual(
            categorize_topic(""),
            'Other Tech News'
        )


class TestStatusDataGeneration(unittest.TestCase):
    """Test status data generation from database"""

    def setUp(self):
        """Create temporary database with test data"""
        self.db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.db_file.name
        self.db_file.close()

        # Create test database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE links (
                id INTEGER PRIMARY KEY,
                date TEXT,
                date_unix INTEGER,
                title TEXT,
                url TEXT,
                source TEXT,
                link_type TEXT,
                episode_date TEXT,
                episode_date_unix INTEGER,
                created_at TEXT,
                ai_category TEXT
            )
        ''')

        # Insert test data
        now = datetime.now()
        recent = now - timedelta(days=30)
        old = now - timedelta(days=200)

        test_links = [
            # Recent showlinks
            (recent, "ChatGPT gets new features", "https://example.com/1", "TechCrunch", "showlink"),
            (recent, "Nvidia announces new chip", "https://example.com/2", "The Verge", "showlink"),
            (recent, "Tesla expands Autopilot", "https://example.com/3", "Bloomberg", "showlink"),
            (recent, "Another AI breakthrough", "https://example.com/4", "TechCrunch", "showlink"),
            (recent, "Gaming news", "https://example.com/5", "The Verge", "showlink"),

            # Recent longreads
            (recent, "Deep dive into AI", "https://example.com/6", "Wired", "longread"),
            (recent, "Future of blockchain", "https://example.com/7", "Medium", "longread"),

            # Old links (should not be in top sources/topics)
            (old, "Old news", "https://example.com/8", "OldSource", "showlink"),
        ]

        for date, title, url, source, link_type in test_links:
            cursor.execute('''
                INSERT INTO links (date, date_unix, title, url, source, link_type, episode_date, episode_date_unix, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                date.strftime("%Y-%m-%d"),
                int(date.timestamp()),
                title,
                url,
                source,
                link_type,
                date.strftime("%Y-%m-%d"),
                int(date.timestamp()),
                now.strftime("%Y-%m-%d %H:%M:%S")
            ))

        conn.commit()
        conn.close()

    def tearDown(self):
        """Clean up temporary database"""
        import os
        os.unlink(self.db_path)

    def test_get_status_data(self):
        """Test that status data is correctly generated"""
        status_data = get_status_data(self.db_path)

        # Check structure
        self.assertIn('last_run', status_data)
        self.assertIn('total_showlinks', status_data)
        self.assertIn('total_longreads', status_data)
        self.assertIn('top_sources', status_data)
        self.assertIn('top_topics', status_data)

        # Check counts
        self.assertEqual(status_data['total_showlinks'], 6)
        self.assertEqual(status_data['total_longreads'], 2)

        # Check top sources (should only include recent ones)
        sources = [s[0] for s in status_data['top_sources']]
        self.assertIn('TechCrunch', sources)
        self.assertIn('The Verge', sources)
        self.assertNotIn('OldSource', sources)  # Too old

        # Check that we get at most 3 sources
        self.assertLessEqual(len(status_data['top_sources']), 3)

        # Check top topics
        topics = [t[0] for t in status_data['top_topics']]
        self.assertIn('AI/Machine Learning', topics)

        # Check that we get at most 3 topics
        self.assertLessEqual(len(status_data['top_topics']), 3)


class TestFormatStatusSection(unittest.TestCase):
    """Test status section formatting"""

    def test_format_status_section(self):
        """Test that status section is correctly formatted as HTML with semantic markup"""
        test_data = {
            'last_run': datetime(2025, 12, 23, 14, 30, 0),
            'total_showlinks': 12065,
            'total_longreads': 1736,
            'top_sources': [
                ('Bloomberg', 112),
                ('The Verge', 87),
                ('WSJ', 62)
            ],
            'top_topics': [
                ('AI/Machine Learning', 404),
                ('Hardware/Chips', 44),
                ('Gaming', 32)
            ]
        }

        result = format_status_section(test_data)

        # Check semantic HTML structure
        self.assertIn('<section class="status-section"', result)
        self.assertIn('aria-labelledby="status-heading"', result)
        self.assertIn('id="status-heading"', result)

        # Check time element with datetime attribute
        self.assertIn('<time datetime="2025-12-23T14:30:00"', result)
        self.assertIn('December 23, 2025', result)

        # Check grid layout structure
        self.assertIn('<div class="status-grid">', result)
        self.assertIn('<div class="status-card">', result)

        # Check data presence
        self.assertIn('12,065', result)
        self.assertIn('1,736', result)
        self.assertIn('Bloomberg', result)
        self.assertIn('112', result)
        self.assertIn('AI/Machine Learning', result)
        self.assertIn('404', result)

        # Check proper list types (ul for archive, ol for sources/topics)
        self.assertIn('<ul class="status-list">', result)
        self.assertIn('<ol class="status-list">', result)

        # Check span elements for styling
        self.assertIn('class="stat-label"', result)
        self.assertIn('stat-value', result)
        self.assertIn('stat-number', result)


class TestUpdateHomepage(unittest.TestCase):
    """Test homepage update functionality"""

    def test_update_homepage_with_markers(self):
        """Test that homepage is correctly updated between markers"""
        # Create temporary homepage
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            f.write("""# Homepage

<!-- STATUS_SECTION -->

Old content here

<!-- END_STATUS_SECTION -->

## Other content

This should remain unchanged.
""")
            temp_path = f.name

        try:
            # Update with new status
            new_status = """## Current Status

**Last Updated:** December 23, 2025

New status content"""

            update_homepage(new_status, temp_path)

            # Read updated file
            with open(temp_path, 'r') as f:
                result = f.read()

            # Check that new content is present
            self.assertIn('New status content', result)
            self.assertNotIn('Old content here', result)

            # Check that other content is preserved
            self.assertIn('## Other content', result)
            self.assertIn('This should remain unchanged', result)

            # Check that markers are preserved
            self.assertIn('<!-- STATUS_SECTION -->', result)
            self.assertIn('<!-- END_STATUS_SECTION -->', result)

        finally:
            import os
            os.unlink(temp_path)

    def test_update_homepage_missing_start_marker(self):
        """Test that error is raised if start marker is missing"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            f.write("""# Homepage

<!-- END_STATUS_SECTION -->
""")
            temp_path = f.name

        try:
            with self.assertRaises(ValueError) as context:
                update_homepage("New content", temp_path)

            self.assertIn('STATUS_SECTION', str(context.exception))

        finally:
            import os
            os.unlink(temp_path)

    def test_update_homepage_missing_end_marker(self):
        """Test that error is raised if end marker is missing"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            f.write("""# Homepage

<!-- STATUS_SECTION -->
""")
            temp_path = f.name

        try:
            with self.assertRaises(ValueError) as context:
                update_homepage("New content", temp_path)

            self.assertIn('END_STATUS_SECTION', str(context.exception))

        finally:
            import os
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()
