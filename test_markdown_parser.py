#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for markdown_parser.py
"""
import unittest
from datetime import datetime
from markdown_parser import (
    parse_date_header,
    parse_date_header_no_year,
    parse_link_bullet,
    extract_year_from_filename
)


class TestDateParsing(unittest.TestCase):
    def test_parse_date_header_with_title(self):
        """Test parsing date header with episode title"""
        line = "**Friday, December 12 2025 - GPT-5.2 As OpenAI's Attempt**"
        result = parse_date_header(line)
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 12)
        self.assertEqual(result.day, 12)

    def test_parse_date_header_without_title(self):
        """Test parsing date header without episode title"""
        line = "**Friday, December 05 2025**"
        result = parse_date_header(line)
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 12)
        self.assertEqual(result.day, 5)

    def test_parse_date_header_no_year(self):
        """Test parsing longreads date format without year"""
        line = "**Friday, December 05**"
        result = parse_date_header_no_year(line, 2024)
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 12)
        self.assertEqual(result.day, 5)

    def test_parse_non_date_line(self):
        """Test that non-date lines return None"""
        line = "This is just regular text"
        result = parse_date_header(line)
        self.assertIsNone(result)


class TestLinkParsing(unittest.TestCase):
    def test_parse_link_with_source(self):
        """Test parsing bullet with source in parentheses"""
        line = "  * [OpenAI Launches GPT-5.2](https://www.wired.com/story/test) (Wired)"
        result = parse_link_bullet(line)
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], "OpenAI Launches GPT-5.2")
        self.assertEqual(result['url'], "https://www.wired.com/story/test")
        self.assertEqual(result['source'], "Wired")

    def test_parse_link_with_source_no_space(self):
        """Test parsing bullet with source directly after URL"""
        line = "  * [Spotify tests AI playlists](https://techcrunch.com/test)(TechCrunch)"
        result = parse_link_bullet(line)
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], "Spotify tests AI playlists")
        self.assertEqual(result['source'], "TechCrunch")

    def test_parse_link_without_source(self):
        """Test parsing bullet without source"""
        line = "  * [Netflix and Hollywood End Game](https://stratechery.com/test)"
        result = parse_link_bullet(line)
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], "Netflix and Hollywood End Game")
        self.assertIsNone(result['source'])

    def test_parse_non_link_line(self):
        """Test that non-link lines return None"""
        line = "Just some regular text"
        result = parse_link_bullet(line)
        self.assertIsNone(result)


class TestFilenameYearExtraction(unittest.TestCase):
    def test_extract_year_from_longreads(self):
        """Test extracting year from longreads filename"""
        self.assertEqual(extract_year_from_filename("longreads-2024.md"), 2024)
        self.assertEqual(extract_year_from_filename("longreads-2023.md"), 2023)

    def test_extract_year_from_showlinks(self):
        """Test extracting year from showlinks filename"""
        self.assertEqual(extract_year_from_filename("all-links-2025.md"), 2025)
        self.assertEqual(extract_year_from_filename("all-links-2022.md"), 2022)

    def test_no_year_in_filename(self):
        """Test files without year return None"""
        self.assertIsNone(extract_year_from_filename("links.md"))
        self.assertIsNone(extract_year_from_filename("README.md"))


if __name__ == '__main__':
    unittest.main()
