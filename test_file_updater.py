#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import tempfile
import os
from datetime import datetime
from file_updater import parse_top_date, find_new_entries, infer_year_from_context


class TestParseDateShowlinks(unittest.TestCase):
    """Test parsing date from showlinks format"""

    def test_parses_showlinks_with_year_and_title(self):
        """Given showlinks format with year and title, should extract datetime"""
        date_str = "**Monday, December 08 2025 - Netflix Faces Hostility**"

        result = parse_top_date(date_str, entry_type='showlinks')

        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 12)
        self.assertEqual(result.day, 8)

    def test_parses_showlinks_different_month(self):
        """Should handle different months correctly"""
        date_str = "**Friday, January 03 2025 - Some Title**"

        result = parse_top_date(date_str, entry_type='showlinks')

        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 3)


class TestParseDateLongreads(unittest.TestCase):
    """Test parsing date from longreads format"""

    def test_parses_longreads_without_year(self):
        """Given longreads format without year, should extract month/day and infer year"""
        date_str = "**Friday, December 05**"

        # Need to provide year context (e.g., 2025)
        result = parse_top_date(date_str, entry_type='longreads', year_context=2025)

        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 12)
        self.assertEqual(result.day, 5)

    def test_parses_longreads_with_year(self):
        """Given longreads format WITH year (new format), should extract datetime"""
        date_str = "**Friday, December 05 2025**"

        result = parse_top_date(date_str, entry_type='longreads')

        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 12)
        self.assertEqual(result.day, 5)

    def test_parses_longreads_with_year_and_suffix(self):
        """Given longreads format with year and abbreviated date suffix, should extract datetime"""
        date_str = "**Friday, December 12 2025 - Fri. 12/12**"

        result = parse_top_date(date_str, entry_type='longreads')

        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 12)
        self.assertEqual(result.day, 12)


class TestParseTopDateFromFile(unittest.TestCase):
    """Test parsing top date from actual markdown files"""

    def test_finds_first_date_after_marker(self):
        """Should find first date after AUTO-GENERATED marker"""
        content = """{% include_relative _includes/showlinks-header.md %}

_Deprecation notice_

 <!-- AUTO-GENERATED CONTENT BELOW -->

**Monday, December 08 2025 - Netflix Faces Hostility**

  * Link 1
  * Link 2

**Friday, December 05 2025 - Older Entry**
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            f.write(content)
            temp_path = f.name

        try:
            result = parse_top_date(temp_path, entry_type='showlinks')

            self.assertIsNotNone(result)
            self.assertEqual(result.year, 2025)
            self.assertEqual(result.month, 12)
            self.assertEqual(result.day, 8)
        finally:
            os.unlink(temp_path)

    def test_returns_none_for_missing_file(self):
        """Should return None when file doesn't exist"""
        result = parse_top_date('/nonexistent/file.md', entry_type='showlinks')

        self.assertIsNone(result)

    def test_returns_none_when_no_marker_found(self):
        """Should return None when AUTO-GENERATED marker is missing"""
        content = """Some content
**Monday, December 08 2025 - Title**
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            f.write(content)
            temp_path = f.name

        try:
            result = parse_top_date(temp_path, entry_type='showlinks')

            self.assertIsNone(result)
        finally:
            os.unlink(temp_path)

    def test_returns_none_when_no_date_after_marker(self):
        """Should return None when marker exists but no date follows"""
        content = """Header

 <!-- AUTO-GENERATED CONTENT BELOW -->

No dates here, just text.
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            f.write(content)
            temp_path = f.name

        try:
            result = parse_top_date(temp_path, entry_type='showlinks')

            self.assertIsNone(result)
        finally:
            os.unlink(temp_path)


class TestFindNewEntries(unittest.TestCase):
    """Test filtering feed entries to find new ones"""

    def create_mock_entry(self, year, month, day):
        """Helper to create mock feed entry at noon UTC to avoid timezone boundary issues"""
        import time
        dt = datetime(year, month, day)
        return {
            'published_parsed': time.struct_time((year, month, day, 12, 0, 0, 0, 0, 0)),
            'title': f'Test Entry {year}-{month:02d}-{day:02d}'
        }

    def test_returns_all_entries_when_top_date_is_none(self):
        """When top_date is None (new file), should return all entries"""
        entries = [
            self.create_mock_entry(2025, 12, 8),
            self.create_mock_entry(2025, 12, 5),
        ]

        result = find_new_entries(entries, top_date=None)

        self.assertEqual(len(result), 2)

    def test_returns_only_newer_entries(self):
        """Should return only entries newer than top_date"""
        entries = [
            self.create_mock_entry(2025, 12, 10),  # Newer
            self.create_mock_entry(2025, 12, 9),   # Newer
            self.create_mock_entry(2025, 12, 8),   # Same as top_date
            self.create_mock_entry(2025, 12, 5),   # Older
        ]
        top_date = datetime(2025, 12, 8)

        result = find_new_entries(entries, top_date)

        self.assertEqual(len(result), 2)
        # Should be in reverse chronological order (newest first)
        self.assertEqual(result[0]['title'], 'Test Entry 2025-12-10')
        self.assertEqual(result[1]['title'], 'Test Entry 2025-12-09')

    def test_returns_empty_when_no_new_entries(self):
        """Should return empty list when all entries are older"""
        entries = [
            self.create_mock_entry(2025, 12, 5),
            self.create_mock_entry(2025, 12, 3),
        ]
        top_date = datetime(2025, 12, 8)

        result = find_new_entries(entries, top_date)

        self.assertEqual(len(result), 0)

    def test_filters_to_target_year_when_top_date_is_none(self):
        """When top_date is None but target_year provided, filter to that year only"""
        entries = [
            self.create_mock_entry(2026, 1, 5),   # 2026
            self.create_mock_entry(2025, 12, 30), # 2025
            self.create_mock_entry(2025, 12, 15), # 2025
            self.create_mock_entry(2024, 12, 20), # 2024
        ]

        result = find_new_entries(entries, top_date=None, target_year=2025)

        self.assertEqual(len(result), 2)
        # Verify only 2025 entries returned
        self.assertEqual(result[0]['title'], 'Test Entry 2025-12-30')
        self.assertEqual(result[1]['title'], 'Test Entry 2025-12-15')

    def test_backward_compatible_returns_all_when_target_year_none(self):
        """When target_year is None (not provided), returns all entries - backward compatible"""
        entries = [
            self.create_mock_entry(2026, 1, 5),
            self.create_mock_entry(2025, 12, 30),
            self.create_mock_entry(2024, 12, 20),
        ]

        result = find_new_entries(entries, top_date=None, target_year=None)

        self.assertEqual(len(result), 3)

    def test_returns_empty_when_no_entries_match_target_year(self):
        """When no entries from target year, returns empty list"""
        entries = [
            self.create_mock_entry(2024, 12, 20),
            self.create_mock_entry(2024, 12, 15),
            self.create_mock_entry(2024, 11, 10),
        ]

        result = find_new_entries(entries, top_date=None, target_year=2025)

        self.assertEqual(len(result), 0)

    def test_ignores_target_year_when_top_date_provided(self):
        """When top_date provided, target_year is ignored - filter by date only"""
        entries = [
            self.create_mock_entry(2025, 12, 10),  # Newer than top_date
            self.create_mock_entry(2024, 12, 15),  # Newer than top_date, but different year
            self.create_mock_entry(2024, 12, 5),   # Older than top_date
        ]
        top_date = datetime(2024, 12, 8)

        # Even though target_year=2025, should return both entries newer than top_date
        result = find_new_entries(entries, top_date=top_date, target_year=2025)

        self.assertEqual(len(result), 2)
        # Should include both 2025 and 2024 entries that are newer than top_date
        self.assertEqual(result[0]['title'], 'Test Entry 2025-12-10')
        self.assertEqual(result[1]['title'], 'Test Entry 2024-12-15')


class TestYearInference(unittest.TestCase):
    """Test year inference logic for longreads"""

    def test_infers_year_from_file_path(self):
        """Should extract year from file path like docs/longreads-2025.md"""
        file_path = "docs/longreads-2025.md"

        result = infer_year_from_context(file_path)

        self.assertEqual(result, 2025)

    def test_infers_year_from_different_path(self):
        """Should work with different year"""
        file_path = "docs/all-links-2024.md"

        result = infer_year_from_context(file_path)

        self.assertEqual(result, 2024)

    def test_returns_current_year_when_no_year_in_path(self):
        """Should fall back to current year when no year in path"""
        file_path = "docs/longreads.md"

        result = infer_year_from_context(file_path)

        # Should return current year
        self.assertEqual(result, datetime.now().year)


class TestMultiYearGrouping(unittest.TestCase):
    """Test grouping entries by year"""

    def test_groups_entries_by_year(self):
        """Should group entries into separate year buckets"""
        import time
        from file_updater import group_entries_by_year

        entries = [
            {'published_parsed': time.struct_time((2025, 12, 9, 10, 0, 0, 0, 0, 0)), 'title': '2025-1'},
            {'published_parsed': time.struct_time((2025, 12, 8, 10, 0, 0, 0, 0, 0)), 'title': '2025-2'},
            {'published_parsed': time.struct_time((2024, 12, 31, 10, 0, 0, 0, 0, 0)), 'title': '2024-1'},
            {'published_parsed': time.struct_time((2024, 12, 30, 10, 0, 0, 0, 0, 0)), 'title': '2024-2'},
        ]

        grouped = group_entries_by_year(entries)

        self.assertEqual(len(grouped), 2)
        self.assertIn(2024, grouped)
        self.assertIn(2025, grouped)
        self.assertEqual(len(grouped[2024]), 2)
        self.assertEqual(len(grouped[2025]), 2)

    def test_handles_single_year(self):
        """Should work correctly with entries from single year"""
        import time
        from file_updater import group_entries_by_year

        entries = [
            {'published_parsed': time.struct_time((2025, 12, 9, 10, 0, 0, 0, 0, 0))},
            {'published_parsed': time.struct_time((2025, 12, 8, 10, 0, 0, 0, 0, 0))},
        ]

        grouped = group_entries_by_year(entries)

        self.assertEqual(len(grouped), 1)
        self.assertIn(2025, grouped)
        self.assertEqual(len(grouped[2025]), 2)


if __name__ == '__main__':
    unittest.main()
