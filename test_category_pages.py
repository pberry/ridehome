#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for category page generator.
"""
import unittest
import sqlite3
import os
from datetime import datetime
from generate_category_pages import category_to_slug, get_links_for_category, generate_category_markdown


class TestCategorySlugGeneration(unittest.TestCase):
    """Test category name to filename slug conversion."""

    def test_converts_ai_machine_learning_to_slug(self):
        """converts 'AI/Machine Learning' to 'ai-machine-learning'"""
        result = category_to_slug('AI/Machine Learning')
        self.assertEqual(result, 'ai-machine-learning')

    def test_converts_hardware_chips_to_slug(self):
        """converts 'Hardware/Chips' to 'hardware-chips'"""
        result = category_to_slug('Hardware/Chips')
        self.assertEqual(result, 'hardware-chips')

    def test_converts_other_tech_news_to_slug(self):
        """converts 'Other Tech News' to 'other-tech-news'"""
        result = category_to_slug('Other Tech News')
        self.assertEqual(result, 'other-tech-news')

    def test_handles_multiple_slashes(self):
        """converts 'Foo/Bar/Baz' to 'foo-bar-baz'"""
        result = category_to_slug('Foo/Bar/Baz')
        self.assertEqual(result, 'foo-bar-baz')


class TestMarkdownGeneration(unittest.TestCase):
    """Test markdown page content generation."""

    def test_generates_page_with_year_and_month_headers(self):
        """generates markdown with h2 years and h3 months in descending order"""
        grouped_links = {
            2025: {
                12: [
                    {'date': '2025-12-15', 'title': 'Link 1', 'url': 'http://example.com/1', 'source': 'Source1'},
                    {'date': '2025-12-10', 'title': 'Link 2', 'url': 'http://example.com/2', 'source': 'Source2'}
                ],
                1: [
                    {'date': '2025-01-20', 'title': 'Link 3', 'url': 'http://example.com/3', 'source': None}
                ]
            },
            2024: {
                12: [
                    {'date': '2024-12-05', 'title': 'Link 4', 'url': 'http://example.com/4', 'source': 'Source4'}
                ]
            }
        }

        result = generate_category_markdown(grouped_links, 'AI/Machine Learning')

        # Check year headers (h2) in descending order
        self.assertIn('## 2025', result)
        self.assertIn('## 2024', result)
        self.assertTrue(result.index('## 2025') < result.index('## 2024'))

        # Check month headers (h3) in descending order within year
        self.assertIn('### December', result)
        self.assertIn('### January', result)
        december_pos = result.index('### December')
        january_pos = result.index('### January')
        self.assertTrue(december_pos < january_pos)

    def test_generates_bullet_list_with_links(self):
        """generates bullet lists with link title, URL, and source"""
        grouped_links = {
            2025: {
                12: [
                    {'date': '2025-12-15', 'title': 'Test Link', 'url': 'http://example.com/test', 'source': 'TestSource'}
                ]
            }
        }

        result = generate_category_markdown(grouped_links, 'AI/Machine Learning')

        # Check bullet list format with markdown link
        self.assertIn('- [Test Link](http://example.com/test) (TestSource)', result)

    def test_handles_missing_source(self):
        """omits source when None"""
        grouped_links = {
            2025: {
                12: [
                    {'date': '2025-12-15', 'title': 'No Source Link', 'url': 'http://example.com/nosource', 'source': None}
                ]
            }
        }

        result = generate_category_markdown(grouped_links, 'AI/Machine Learning')

        # Should have link without source parentheses
        self.assertIn('- [No Source Link](http://example.com/nosource)', result)
        self.assertNotIn('(None)', result)

    def test_includes_jekyll_front_matter(self):
        """includes Jekyll front matter with category title"""
        grouped_links = {
            2025: {
                12: [{'date': '2025-12-15', 'title': 'Link', 'url': 'http://example.com', 'source': 'S'}]
            }
        }

        result = generate_category_markdown(grouped_links, 'AI/Machine Learning')

        # Check Jekyll front matter
        self.assertTrue(result.startswith('---\n'))
        self.assertIn('title: AI/Machine Learning', result)


class TestDatabaseQuery(unittest.TestCase):
    """Test database queries for category links."""

    def setUp(self):
        """Create test database with sample data."""
        self.test_db = 'test_category.db'
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()

        # Create minimal schema
        cursor.execute('''
            CREATE TABLE links (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                date_unix INTEGER NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                source TEXT,
                ai_category TEXT
            )
        ''')

        # Insert test data: 3 links in AI/ML category across 2 years, 2 months
        test_data = [
            ('2025-12-15', 1734220800, 'Link Dec 2025', 'http://example.com/1', 'Source1', 'AI/Machine Learning'),
            ('2025-01-10', 1736467200, 'Link Jan 2025', 'http://example.com/2', 'Source2', 'AI/Machine Learning'),
            ('2024-12-05', 1733356800, 'Link Dec 2024', 'http://example.com/3', 'Source3', 'AI/Machine Learning'),
        ]
        cursor.executemany('INSERT INTO links (date, date_unix, title, url, source, ai_category) VALUES (?, ?, ?, ?, ?, ?)', test_data)
        conn.commit()
        conn.close()

    def tearDown(self):
        """Remove test database."""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_groups_links_by_year_and_month_descending(self):
        """returns links grouped by year (desc) then month (desc)"""
        result = get_links_for_category(self.test_db, 'AI/Machine Learning')

        # Expected structure: {2025: {12: [...], 1: [...]}, 2024: {12: [...]}}
        self.assertIn(2025, result)
        self.assertIn(2024, result)

        # Year 2025 should have months 12 and 1
        self.assertIn(12, result[2025])
        self.assertIn(1, result[2025])

        # Year 2024 should have month 12
        self.assertIn(12, result[2024])

        # Check links in Dec 2025
        dec_2025_links = result[2025][12]
        self.assertEqual(len(dec_2025_links), 1)
        self.assertEqual(dec_2025_links[0]['title'], 'Link Dec 2025')

    def test_returns_empty_dict_for_nonexistent_category(self):
        """returns empty dict when category has no links"""
        result = get_links_for_category(self.test_db, 'Nonexistent Category')
        self.assertEqual(result, {})


if __name__ == '__main__':
    unittest.main()
