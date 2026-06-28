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
        self.assertEqual(len(_all_months_in_range(24)), 24)

    def test_sorted_oldest_first(self):
        months = _all_months_in_range(12)
        self.assertEqual(months, sorted(months))

    def test_format(self):
        for m in _all_months_in_range(3):
            self.assertRegex(m, r'^\d{4}-\d{2}$')

    def test_ends_with_current_month(self):
        months = _all_months_in_range(6)
        self.assertEqual(months[-1], datetime.now().strftime('%Y-%m'))


class TestGetTopSources(unittest.TestCase):

    def setUp(self):
        today = datetime.now().strftime('%Y-%m-%d')
        old = (datetime.now() - timedelta(days=800)).strftime('%Y-%m-%d')
        links = (
            [(today, 'Bloomberg')] * 5 +
            [(today, 'The Verge')] * 3 +
            [(today, 'TechCrunch')] +
            [(today, None)] * 10 +       # NULL — must be excluded
            [(old, 'Bloomberg')] * 100   # outside lookback — must be excluded
        )
        self.db_path = _make_test_db(links)

    def tearDown(self):
        os.unlink(self.db_path)

    def test_ordered_by_count_descending(self):
        sources = [s for s, _ in get_top_sources(self.db_path, n=3, lookback_months=24)]
        self.assertEqual(sources, ['Bloomberg', 'The Verge', 'TechCrunch'])

    def test_correct_counts(self):
        results = dict(get_top_sources(self.db_path, n=3, lookback_months=24))
        self.assertEqual(results['Bloomberg'], 5)
        self.assertEqual(results['The Verge'], 3)
        self.assertEqual(results['TechCrunch'], 1)

    def test_excludes_null_source(self):
        results = dict(get_top_sources(self.db_path, n=10, lookback_months=24))
        self.assertNotIn(None, results)

    def test_respects_lookback_window(self):
        results = dict(get_top_sources(self.db_path, n=3, lookback_months=24))
        self.assertEqual(results['Bloomberg'], 5)  # not 105

    def test_respects_top_n_limit(self):
        self.assertEqual(len(get_top_sources(self.db_path, n=2, lookback_months=24)), 2)


class TestGetMonthlyCounts(unittest.TestCase):

    def setUp(self):
        today = datetime.now()
        this_month = today.strftime('%Y-%m-%d')
        self.this_month_str = today.strftime('%Y-%m')

        # Pick a date 2 months back (safe across year boundaries)
        m = today.month - 2
        y = today.year
        if m <= 0:
            m += 12
            y -= 1
        two_months_ago = today.replace(year=y, month=m, day=1).strftime('%Y-%m-%d')
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
        for month, count in result['The Verge'].items():
            if month != self.this_month_str:
                self.assertEqual(count, 0, f'Expected 0 for {month}, got {count}')

    def test_all_months_present(self):
        result = get_monthly_counts(self.db_path, ['Bloomberg'], lookback_months=24)
        self.assertEqual(len(result['Bloomberg']), 24)

    def test_returns_empty_for_no_sources(self):
        self.assertEqual(get_monthly_counts(self.db_path, [], lookback_months=24), {})


class TestShouldRegenerate(unittest.TestCase):

    def setUp(self):
        tf = tempfile.NamedTemporaryFile(delete=False, suffix='.state')
        self.state_file = tf.name
        tf.close()
        os.unlink(self.state_file)

    def tearDown(self):
        if os.path.exists(self.state_file):
            os.unlink(self.state_file)

    def test_true_when_no_state_file(self):
        self.assertTrue(should_regenerate(self.state_file))

    def test_false_when_current_month(self):
        with open(self.state_file, 'w') as f:
            f.write(datetime.now().strftime('%Y-%m'))
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
        result = _nudge_labels([0.0, 5.0, 10.0], min_gap=1.5)
        for expected, actual in zip([0.0, 5.0, 10.0], result):
            self.assertAlmostEqual(actual, expected, places=3)

    def test_nudges_apart_when_too_close(self):
        result = _nudge_labels([5.0, 5.1, 5.2], min_gap=1.5)
        for i in range(1, len(result)):
            self.assertGreaterEqual(result[i] - result[i - 1], 1.4)

    def test_preserves_order(self):
        result = _nudge_labels([1.0, 1.2, 8.0], min_gap=1.5)
        self.assertEqual(result, sorted(result))


class TestGenerateRacePlotSVG(unittest.TestCase):
    """Smoke test: generate_race_plot produces a non-empty SVG file."""

    def setUp(self):
        today = datetime.now()
        # Spread links across a few months so there's enough data to plot
        links = []
        for delta_months in range(5):
            m = today.month - delta_months
            y = today.year
            if m <= 0:
                m += 12
                y -= 1
            date_str = today.replace(year=y, month=m, day=1).strftime('%Y-%m-%d')
            for src in ['Bloomberg', 'The Verge', 'TechCrunch']:
                links.extend([(date_str, src)] * 15)

        self.db_path = _make_test_db(links)
        self.out_file = tempfile.NamedTemporaryFile(
            delete=False, suffix='.svg'
        ).name

    def tearDown(self):
        os.unlink(self.db_path)
        if os.path.exists(self.out_file):
            os.unlink(self.out_file)

    def test_creates_svg_file(self):
        from source_race_plot import generate_race_plot
        generate_race_plot(
            db_path=self.db_path,
            output_path=self.out_file,
            top_n=3,
            lookback_months=6,
        )
        self.assertTrue(os.path.exists(self.out_file))
        self.assertGreater(os.path.getsize(self.out_file), 0)

    def test_output_is_valid_svg(self):
        from source_race_plot import generate_race_plot
        generate_race_plot(
            db_path=self.db_path,
            output_path=self.out_file,
            top_n=3,
            lookback_months=6,
        )
        with open(self.out_file, 'r') as f:
            content = f.read()
        self.assertIn('<svg', content)


if __name__ == '__main__':
    unittest.main()
