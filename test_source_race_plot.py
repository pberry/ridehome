#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for source_race_plot.py
"""
import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta

from source_race_plot import (
    get_top_sources,
    get_monthly_counts,
    should_regenerate,
    mark_as_run,
    _all_months_in_range,
    _nudge_labels,
)


def _make_test_db(links):
    """Create a temp SQLite DB with the links schema and insert given rows."""
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_path = db_file.name
    db_file.close()

    conn = sqlite3.connect(db_path)
    conn.execute('''
        CREATE TABLE links (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            date_unix INTEGER NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            source TEXT,
            link_type TEXT NOT NULL,
            episode_date TEXT NOT NULL,
            episode_date_unix INTEGER NOT NULL,
            created_at TEXT
        )
    ''')
    for date_str, source in links:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        conn.execute(
            'INSERT INTO links (date, date_unix, title, url, source, link_type, episode_date, episode_date_unix) VALUES (?,?,?,?,?,?,?,?)',
            (date_str, int(dt.timestamp()), 'Test', f'https://example.com/{date_str}', source, 'showlink', date_str, int(dt.timestamp()))
        )
    conn.commit()
    conn.close()
    return db_path


class TestAllMonthsInRange(unittest.TestCase):

    def test_length(self):
        months = _all_months_in_range(24)
        self.assertEqual(len(months), 24)

    def test_sorted_oldest_first(self):
        months = _all_months_in_range(12)
        self.assertEqual(months, sorted(months))

    def test_format(self):
        months = _all_months_in_range(3)
        for m in months:
            self.assertRegex(m, r'^\d{4}-\d{2}$')

    def test_ends_with_current_month(self):
        months = _all_months_in_range(6)
        self.assertEqual(months[-1], datetime.now().strftime('%Y-%m'))


class TestGetTopSources(unittest.TestCase):

    def setUp(self):
        today = datetime.now().strftime('%Y-%m-%d')
        one_month_ago = (datetime.now() - timedelta(days=35)).strftime('%Y-%m-%d')
        old = (datetime.now() - timedelta(days=800)).strftime('%Y-%m-%d')

        links = (
            # Bloomberg: 5 recent
            [(today, 'Bloomberg')] * 5 +
            # The Verge: 3 recent
            [(today, 'The Verge')] * 3 +
            # TechCrunch: 1 recent
            [(today, 'TechCrunch')] +
            # NULL source (should be excluded)
            [(today, None)] * 10 +
            # Old link outside lookback window (should be excluded)
            [(old, 'Bloomberg')] * 100
        )
        self.db_path = _make_test_db(links)

    def tearDown(self):
        os.unlink(self.db_path)

    def test_ordered_by_count_descending(self):
        results = get_top_sources(self.db_path, n=3, lookback_months=24)
        sources = [s for s, _ in results]
        self.assertEqual(sources[0], 'Bloomberg')
        self.assertEqual(sources[1], 'The Verge')
        self.assertEqual(sources[2], 'TechCrunch')

    def test_correct_counts(self):
        results = dict(get_top_sources(self.db_path, n=3, lookback_months=24))
        self.assertEqual(results['Bloomberg'], 5)
        self.assertEqual(results['The Verge'], 3)
        self.assertEqual(results['TechCrunch'], 1)

    def test_excludes_null_source(self):
        results = dict(get_top_sources(self.db_path, n=10, lookback_months=24))
        self.assertNotIn(None, results)

    def test_respects_lookback_window(self):
        # Old Bloomberg links (800 days ago) should not appear with 24-month lookback
        results = dict(get_top_sources(self.db_path, n=3, lookback_months=24))
        # Bloomberg should only have 5 (recent), not 105
        self.assertEqual(results['Bloomberg'], 5)

    def test_respects_top_n_limit(self):
        results = get_top_sources(self.db_path, n=2, lookback_months=24)
        self.assertEqual(len(results), 2)


class TestGetMonthlyCounts(unittest.TestCase):

    def setUp(self):
        # Insert links in two known months
        today = datetime.now()
        this_month = today.strftime('%Y-%m-%d')
        # Pick a date 2 months ago
        if today.month > 2:
            two_months_ago = today.replace(month=today.month - 2).strftime('%Y-%m-%d')
        elif today.month == 2:
            two_months_ago = today.replace(year=today.year - 1, month=12).strftime('%Y-%m-%d')
        else:
            two_months_ago = today.replace(year=today.year - 1, month=today.month + 10).strftime('%Y-%m-%d')

        self.this_month_str = today.strftime('%Y-%m')
        self.two_months_ago_str = two_months_ago[:7]

        links = (
            [(this_month, 'Bloomberg')] * 4 +
            [(this_month, 'The Verge')] * 2 +
            [(two_months_ago, 'Bloomberg')] * 7
        )
        self.db_path = _make_test_db(links)

    def tearDown(self):
        os.unlink(self.db_path)

    def test_correct_counts_this_month(self):
        result = get_monthly_counts(self.db_path, ['Bloomberg', 'The Verge'], lookback_months=24)
        self.assertEqual(result['Bloomberg'][self.this_month_str], 4)
        self.assertEqual(result['The Verge'][self.this_month_str], 2)

    def test_correct_counts_earlier_month(self):
        result = get_monthly_counts(self.db_path, ['Bloomberg'], lookback_months=24)
        self.assertEqual(result['Bloomberg'][self.two_months_ago_str], 7)

    def test_zero_fill_missing_months(self):
        result = get_monthly_counts(self.db_path, ['The Verge'], lookback_months=24)
        # The Verge only has data this month; all prior months should be 0
        verge_counts = result['The Verge']
        for month, count in verge_counts.items():
            if month != self.this_month_str:
                self.assertEqual(count, 0, f'Expected 0 for {month}, got {count}')

    def test_all_months_present(self):
        result = get_monthly_counts(self.db_path, ['Bloomberg'], lookback_months=24)
        months = list(result['Bloomberg'].keys())
        self.assertEqual(len(months), 24)

    def test_returns_empty_for_no_sources(self):
        result = get_monthly_counts(self.db_path, [], lookback_months=24)
        self.assertEqual(result, {})


class TestShouldRegenerate(unittest.TestCase):

    def setUp(self):
        self.state_file = tempfile.NamedTemporaryFile(delete=False, suffix='.state').name
        os.unlink(self.state_file)  # start with no file

    def tearDown(self):
        if os.path.exists(self.state_file):
            os.unlink(self.state_file)

    def test_true_when_no_state_file(self):
        self.assertTrue(should_regenerate(self.state_file))

    def test_false_when_current_month(self):
        current = datetime.now().strftime('%Y-%m')
        with open(self.state_file, 'w') as f:
            f.write(current)
        self.assertFalse(should_regenerate(self.state_file))

    def test_true_when_old_month(self):
        with open(self.state_file, 'w') as f:
            f.write('2024-01')
        self.assertTrue(should_regenerate(self.state_file))

    def test_mark_as_run_creates_state(self):
        mark_as_run(self.state_file)
        self.assertTrue(os.path.exists(self.state_file))
        self.assertFalse(should_regenerate(self.state_file))


class TestNudgeLabels(unittest.TestCase):

    def test_no_change_when_spaced(self):
        positions = [0.0, 5.0, 10.0]
        result = _nudge_labels(positions, min_gap=1.5)
        self.assertAlmostEqual(result[0], 0.0, places=3)
        self.assertAlmostEqual(result[1], 5.0, places=3)
        self.assertAlmostEqual(result[2], 10.0, places=3)

    def test_nudges_apart_when_too_close(self):
        positions = [5.0, 5.1, 5.2]
        result = _nudge_labels(positions, min_gap=1.5)
        for i in range(1, len(result)):
            self.assertGreaterEqual(result[i] - result[i - 1], 1.4)

    def test_preserves_order(self):
        positions = [1.0, 1.2, 8.0]
        result = _nudge_labels(positions, min_gap=1.5)
        self.assertEqual(result, sorted(result))


if __name__ == '__main__':
    unittest.main()
