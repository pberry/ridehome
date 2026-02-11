#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for verifying relative vs absolute link paths.

Site is deployed at pberry.github.io/ridehome/ (subpath).
All internal links must be relative, not absolute.
Absolute links starting with / resolve to pberry.github.io/ instead of pberry.github.io/ridehome/
"""
import unittest
import sqlite3
import os
import re
from generate_index import format_recent_shows_section
from generate_year_pages import generate_markdown_content, PAGE_CONFIGS


class TestIndexCategoryLinks(unittest.TestCase):
    """Test index.md category links are relative, not absolute."""

    def test_recent_episode_category_links_are_relative(self):
        """category links in recent episode use relative paths"""
        episode_data = {
            'date': '2025-01-10',
            'episode_title': 'Test Episode',
            'links': [
                {
                    'title': 'AI News',
                    'url': 'https://example.com/ai',
                    'source': 'TechNews',
                    'ai_category': 'AI/Machine Learning'
                }
            ]
        }

        result = format_recent_shows_section(episode_data)

        # Should NOT contain absolute path
        self.assertNotIn('href="/categories/', result,
                         "Category links must not start with / (absolute path)")

        # Should contain relative path
        self.assertIn('href="categories/ai-machine-learning.html"', result,
                      "Category links must use relative path")

    def test_multiple_categories_all_use_relative_paths(self):
        """all category links use relative paths when multiple categories present"""
        episode_data = {
            'date': '2025-01-10',
            'episode_title': 'Test Episode',
            'links': [
                {
                    'title': 'AI News',
                    'url': 'https://example.com/ai',
                    'source': 'TechNews',
                    'ai_category': 'AI/Machine Learning'
                },
                {
                    'title': 'Cloud News',
                    'url': 'https://example.com/cloud',
                    'source': 'CloudBlog',
                    'ai_category': 'Cloud/Enterprise'
                },
                {
                    'title': 'Security Alert',
                    'url': 'https://example.com/security',
                    'source': 'SecNews',
                    'ai_category': 'Security/Privacy'
                }
            ]
        }

        result = format_recent_shows_section(episode_data)

        # Extract all category hrefs
        category_hrefs = re.findall(r'href="([^"]*categories/[^"]*)"', result)

        # Verify at least 3 category links found
        self.assertGreaterEqual(len(category_hrefs), 3,
                                "Should find category links for all 3 items")

        # Verify NONE start with /
        absolute_paths = [href for href in category_hrefs if href.startswith('/')]
        self.assertEqual(absolute_paths, [],
                         f"Found absolute paths: {absolute_paths}")

    def test_no_category_links_when_ai_category_missing(self):
        """no category links generated when ai_category is None"""
        episode_data = {
            'date': '2025-01-10',
            'episode_title': 'Test Episode',
            'links': [
                {
                    'title': 'News Without Category',
                    'url': 'https://example.com/news',
                    'source': 'NewsSource',
                    'ai_category': None
                }
            ]
        }

        result = format_recent_shows_section(episode_data)

        # Should not contain any category links
        self.assertNotIn('categories/', result,
                         "No category links when ai_category is None")


class TestYearPageCategoryLinks(unittest.TestCase):
    """Test year pages sidebar category links are relative, not absolute."""

    def setUp(self):
        """Create test database with sample data."""
        self.test_db = 'test_link_paths.db'
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()

        # Create minimal schema matching real database
        cursor.execute('''
            CREATE TABLE links (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                date_unix INTEGER NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                source TEXT,
                ai_category TEXT,
                link_type TEXT NOT NULL,
                episode_title TEXT
            )
        ''')

        # Insert test data
        test_data = [
            ('2025-01-10', 1736467200, 'Link 1', 'http://example.com/1', 'Source1', 'AI/Machine Learning', 'showlink', 'Episode 1'),
            ('2025-01-09', 1736380800, 'Link 2', 'http://example.com/2', 'Source2', 'Hardware/Chips', 'showlink', 'Episode 2'),
        ]
        cursor.executemany(
            'INSERT INTO links (date, date_unix, title, url, source, ai_category, link_type, episode_title) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            test_data
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        """Remove test database."""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_year_page_includes_category_sidebar(self):
        """year page for showlinks includes category sidebar"""
        from generate_year_pages import get_links_for_year

        config = PAGE_CONFIGS['showlinks']
        links = get_links_for_year(self.test_db, 2025, config['link_type'])

        result = generate_markdown_content(2025, config['link_type'], links, config, self.test_db)

        self.assertIn('{% include categories/sidebar.html %}', result,
                      "Showlinks year page should include category sidebar")

    def test_sidebar_html_category_links_use_base_path(self):
        """sidebar.html category links include /ridehome/ base path"""
        sidebar_path = os.path.join('docs', '_includes', 'categories', 'sidebar.html')
        with open(sidebar_path) as f:
            sidebar_html = f.read()

        category_hrefs = re.findall(r'<li><a href="([^"]*)"', sidebar_html)

        self.assertGreater(len(category_hrefs), 0,
                           "Should find category links in sidebar")

        # All links should use /ridehome/ base path for GitHub Pages subpath deployment
        for href in category_hrefs:
            self.assertTrue(href.startswith('/ridehome/categories/'),
                            f"Sidebar link should use /ridehome/ base path: {href}")


if __name__ == '__main__':
    unittest.main()
