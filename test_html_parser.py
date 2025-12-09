#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from html_parser import find_section, find_links_section


class TestLinksExtraction(unittest.TestCase):
    """Test extraction of links from HTML content"""

    def test_extracts_ul_after_links_paragraph(self):
        """Given HTML with 'Links:' paragraph followed by <ul>, should return the <ul> element"""
        html = '''
            <p>Links:</p>
            <ul>
                <li><a href="https://example.com/1">First Article</a> (Source)</li>
                <li><a href="https://example.com/2">Second Article</a> (Another Source)</li>
            </ul>
        '''

        result = find_links_section(html)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, 'ul')
        links = result.find_all('a')
        self.assertEqual(len(links), 2)

    def test_fallback_to_single_ul_when_no_links_paragraph(self):
        """Given HTML with no 'Links:' paragraph but one <ul>, should return that <ul>"""
        html = '''
            <p>Some intro text about the episode.</p>
            <ul>
                <li><a href="https://example.com/link">Single link</a></li>
            </ul>
        '''

        result = find_links_section(html)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, 'ul')

    def test_returns_none_when_multiple_ul_blocks_and_no_links_paragraph(self):
        """Given HTML with multiple <ul> blocks and no 'Links:' paragraph, should return None"""
        html = '''
            <p>Some intro text</p>
            <ul>
                <li>First list item</li>
            </ul>
            <p>More text</p>
            <ul>
                <li>Second list item</li>
            </ul>
        '''

        result = find_links_section(html)

        self.assertIsNone(result)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""

    def test_plain_text_content_returns_none(self):
        """Given plain text without HTML tags, should return None gracefully"""
        # Real example from September 5, 2025 episode (text/plain instead of text/html)
        plain_text = '''From the, this wasn't on my bingo card file, OpenAI has launched a sort of job board?

Links:


OpenAI Plans Jobs Platform, Certification Program for AI Roles (Bloomberg)


OpenAI set to start mass production of its own AI chips with Broadcom (FT)

Weekend Longreads Suggestions:


State of the software engineering job market in 2025 (The Pragmatic Engineer)
'''

        result = find_links_section(plain_text)

        # Should return None because there are no HTML <p> or <ul> tags
        self.assertIsNone(result)

    def test_timestamp_does_not_match_longreads_pattern(self):
        """Timestamp like '15:35 Longreads' should NOT match, only 'Weekend Longreads' should"""
        # Real bug from September 5, 2025 episode
        html = '''
            <p><strong>15:35 Longreads</strong></p>
            <p>Links:</p>
            <ul>
                <li><a href="https://example.com/link1">Regular Link</a></li>
            </ul>
            <p>Weekend Longreads Suggestions:</p>
            <ul>
                <li><a href="https://example.com/longread1">Actual Longread</a></li>
            </ul>
        '''

        result = find_section(html, pattern="Weekend Longreads|Longreads Suggestions")

        # Should match "Weekend Longreads Suggestions:", NOT "15:35 Longreads" timestamp
        self.assertIsNotNone(result)
        links = result.find_all('a')
        # Should find the actual longread, not the regular link
        self.assertEqual(len(links), 1)
        self.assertIn('Actual Longread', links[0].get_text())

    def test_intro_paragraph_does_not_match_when_standalone_header_exists(self):
        """Should match standalone header, not intro paragraph that mentions the section"""
        # Real bug from August 29, 2025 episode
        html = '''
            <p><em><strong>Intro text mentioning the Weekend Longreads Suggestions.</strong></em></p>
            <p>Links:</p>
            <ul>
                <li><a href="https://example.com/link1">Regular Link 1</a></li>
                <li><a href="https://example.com/link2">Regular Link 2</a></li>
            </ul>
            <p>Weekend Longreads Suggestions</p>
            <ul>
                <li><a href="https://example.com/longread1">Actual Longread</a></li>
            </ul>
        '''

        result = find_section(html, pattern="Weekend Longreads|Longreads Suggestions")

        # Should match standalone "Weekend Longreads Suggestions" header, NOT the intro paragraph
        self.assertIsNotNone(result)
        links = result.find_all('a')
        # Should find 1 longread link, not the 2 regular links
        self.assertEqual(len(links), 1)
        self.assertIn('Actual Longread', links[0].get_text())

    def test_chooses_paragraph_followed_by_ul_not_just_shortest(self):
        """Should match paragraph followed by <ul>, using structure not just text length"""
        # Edge case: short paragraph without <ul> vs longer paragraph with <ul>
        html = '''
            <p>Short text mentioning Longreads here</p>
            <p>Some other paragraph</p>
            <p>Weekend Longreads Suggestions for this week</p>
            <ul>
                <li><a href="https://example.com/longread1">Actual Longread</a></li>
            </ul>
        '''

        result = find_section(html, pattern="Weekend Longreads|Longreads|Suggestions")

        # Should match the paragraph followed by <ul>, even though it's longer
        self.assertIsNotNone(result)
        self.assertEqual(result.name, 'ul')
        links = result.find_all('a')
        self.assertEqual(len(links), 1)
        self.assertIn('Actual Longread', links[0].get_text())

    def test_multiple_paragraphs_with_ul_chooses_shortest(self):
        """When multiple paragraphs have <ul> next sibling, choose shortest (header not intro)"""
        # Real bug from November 26, 2025 episode
        html = '''
            <p><em><strong>Intro mentioning the Weekend Longreads Suggestions.</strong></em></p>
            <ul>
                <li><a href="https://example.com/link1">Regular Link 1</a></li>
                <li><a href="https://example.com/link2">Regular Link 2</a></li>
                <li><a href="https://example.com/link3">Regular Link 3</a></li>
                <li><a href="https://example.com/link4">Regular Link 4</a></li>
                <li><a href="https://example.com/link5">Regular Link 5</a></li>
                <li><a href="https://example.com/link6">Regular Link 6</a></li>
            </ul>
            <p>Weekend Longreads Suggestions:</p>
            <ul>
                <li><a href="https://example.com/longread1">Longread 1</a></li>
                <li><a href="https://example.com/longread2">Longread 2</a></li>
                <li><a href="https://example.com/longread3">Longread 3</a></li>
            </ul>
        '''

        result = find_section(html, pattern="Weekend Longreads|Longreads Suggestions")

        # Should match shortest paragraph with <ul> next sibling (the header, not the intro)
        self.assertIsNotNone(result)
        self.assertEqual(result.name, 'ul')
        links = result.find_all('a')
        # Should find 3 longreads, not 6 regular links
        self.assertEqual(len(links), 3)
        self.assertIn('Longread 1', links[0].get_text())


class TestGeneralizedSectionFinding(unittest.TestCase):
    """Test finding sections by custom patterns"""

    def test_finds_weekend_longreads_section(self):
        """Given HTML with 'Weekend Longreads' paragraph, should return the <ul> element"""
        html = '''
            <p>Weekend Longreads Suggestions:</p>
            <ul>
                <li><a href="https://example.com/longread1">Long Article</a> (NYTimes)</li>
                <li><a href="https://example.com/longread2">Deep Dive</a> (Wired)</li>
            </ul>
        '''

        result = find_section(html, pattern="Weekend Longreads")

        self.assertIsNotNone(result)
        self.assertEqual(result.name, 'ul')
        links = result.find_all('a')
        self.assertEqual(len(links), 2)

    def test_finds_weekend_longreads_after_regular_links(self):
        """Friday episodes: should find Weekend Longreads section, not the first UL with regular links"""
        html = '''
            <p><strong>Episode intro mentioning Weekend Longreads suggestions.</strong></p>
            <ul>
                <li><a href="https://example.com/link1">Regular Link 1</a> (Source)</li>
                <li><a href="https://example.com/link2">Regular Link 2</a> (Source)</li>
                <li><a href="https://example.com/link3">Regular Link 3</a> (Source)</li>
            </ul>
            <p>Weekend Longreads Suggestions:</p>
            <ul>
                <li><a href="https://example.com/longread1">Longread 1</a> (NYTimes)</li>
                <li><a href="https://example.com/longread2">Longread 2</a> (Wired)</li>
            </ul>
        '''

        result = find_section(html, pattern="Weekend Longreads Suggestions")

        self.assertIsNotNone(result)
        self.assertEqual(result.name, 'ul')
        links = result.find_all('a')
        # Should find the longreads UL (2 links), NOT the regular links UL (3 links)
        self.assertEqual(len(links), 2)
        # Verify it's the longreads section
        self.assertIn('Longread 1', links[0].get_text())


if __name__ == '__main__':
    unittest.main()
