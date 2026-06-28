#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Source Race Plot — Horse Race chart of top news sources over time.
Generates an SVG line chart showing monthly link counts for the top N sources
over the last 24 months.

Usage:
    uv run source_race_plot.py           # Generate (idempotent per month)
    uv run source_race_plot.py --force   # Force regeneration
    uv run source_race_plot.py --top 15  # Show top 15 sources
    uv run source_race_plot.py --output docs/assets/source-race.svg
"""
import argparse
import os
import sqlite3
import sys
from datetime import datetime, date

import matplotlib
matplotlib.use('Agg')
# Use browser fonts — keeps the SVG small and lets the page's own font stack
# render the text, so it matches the surrounding typography exactly.
matplotlib.rcParams['svg.fonttype'] = 'none'
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = [
    '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Helvetica Neue',
    'Helvetica', 'Arial', 'sans-serif',
]
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ── Solarized Light palette (matches docs/assets/main.scss) ──────────────────
_BG_PRIMARY   = '#fdf6e3'  # base3  — page background
_BG_SECONDARY = '#eee8d5'  # base2  — card / legend background
_TEXT_PRIMARY   = '#556873'  # base00-accessible — body text
_TEXT_SECONDARY = '#485e6a'  # base01-accessible — headings
_BORDER_COLOR   = '#93a1a1'  # base1  — borders and grid lines

# Solarized accent colors for the race lines, in visual-distinctiveness order
_LINE_COLORS = [
    '#268bd2',  # blue
    '#dc322f',  # red
    '#2aa198',  # cyan
    '#d33682',  # magenta
    '#859900',  # green
    '#b58900',  # yellow
    '#6c71c4',  # violet
    '#cb4b16',  # orange
    '#586e75',  # base01 — dark slate (9th source)
    '#073642',  # base02 — very dark teal (10th source)
]

STATE_FILE = '.source_race_last_run'
DEFAULT_DB = 'ridehome.db'
DEFAULT_OUTPUT = 'docs/assets/source-race.svg'
DEFAULT_TOP_N = 10
DEFAULT_LOOKBACK = 24
MIN_MONTH_TOTAL = 50  # exclude first month if too few links (likely a partial month)


def get_top_sources(db_path, n=DEFAULT_TOP_N, lookback_months=DEFAULT_LOOKBACK):
    """Return list of (source, total_count) for the top N sources in the lookback window."""
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(
            """
            SELECT source, COUNT(*) AS total
            FROM links
            WHERE source IS NOT NULL
              AND date >= date('now', ?)
            GROUP BY source
            ORDER BY total DESC
            LIMIT ?
            """,
            (f'-{lookback_months} months', n)
        ).fetchall()
    finally:
        conn.close()


def _all_months_in_range(lookback_months):
    """Return sorted list of 'YYYY-MM' strings for the last N months, oldest first."""
    today = date.today()
    months = []
    year, month = today.year, today.month
    for _ in range(lookback_months):
        months.append(f'{year:04d}-{month:02d}')
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    months.reverse()
    return months


def get_monthly_counts(db_path, sources, lookback_months=DEFAULT_LOOKBACK):
    """
    Return dict {source: {month: count}} for every month in the lookback window.
    Months with no links for a source are zero-filled.
    """
    if not sources:
        return {}

    placeholders = ','.join('?' * len(sources))
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            f"""
            SELECT strftime('%Y-%m', date) AS month, source, COUNT(*) AS cnt
            FROM links
            WHERE source IS NOT NULL
              AND date >= date('now', ?)
              AND source IN ({placeholders})
            GROUP BY month, source
            ORDER BY month
            """,
            [f'-{lookback_months} months'] + list(sources)
        ).fetchall()
    finally:
        conn.close()

    all_months = _all_months_in_range(lookback_months)
    result = {src: {m: 0 for m in all_months} for src in sources}
    for month, source, count in rows:
        if month in result.get(source, {}):
            result[source][month] = count
    return result


def should_regenerate(state_file=STATE_FILE):
    """Return True if no plot has been generated this calendar month."""
    current = datetime.now().strftime('%Y-%m')
    if not os.path.exists(state_file):
        return True
    with open(state_file, 'r') as f:
        return f.read().strip() != current


def mark_as_run(state_file=STATE_FILE):
    """Record that we generated the plot this month."""
    with open(state_file, 'w') as f:
        f.write(datetime.now().strftime('%Y-%m'))


def _nudge_labels(positions, min_gap=1.5):
    """
    Iteratively spread y-positions apart so no two are closer than min_gap.
    Returns a new list preserving the original order.
    """
    pos = list(positions)
    for _ in range(50):
        changed = False
        for i in range(1, len(pos)):
            if pos[i] - pos[i - 1] < min_gap:
                mid = (pos[i] + pos[i - 1]) / 2
                pos[i - 1] = mid - min_gap / 2
                pos[i] = mid + min_gap / 2
                changed = True
        if not changed:
            break
    return pos


def generate_race_plot(
    db_path=DEFAULT_DB,
    output_path=DEFAULT_OUTPUT,
    top_n=DEFAULT_TOP_N,
    lookback_months=DEFAULT_LOOKBACK,
):
    """Generate the horse race SVG and save to output_path."""
    top_sources_data = get_top_sources(db_path, top_n, lookback_months)
    if not top_sources_data:
        print('No source data found.')
        return

    source_names = [s for s, _ in top_sources_data]
    source_totals = {s: t for s, t in top_sources_data}

    monthly = get_monthly_counts(db_path, source_names, lookback_months)
    all_months = _all_months_in_range(lookback_months)

    # Drop the first month if it looks like a partial boundary month
    if all_months:
        first_total = sum(monthly[src].get(all_months[0], 0) for src in source_names)
        if first_total < MIN_MONTH_TOTAL:
            all_months = all_months[1:]

    if not all_months:
        print('Not enough monthly data to plot.')
        return

    def fmt_month(ym):
        return datetime.strptime(ym, '%Y-%m').strftime("%b\n'%y")

    x_labels = [fmt_month(m) for m in all_months]
    x_pos = list(range(len(all_months)))
    x_last = len(all_months) - 1

    colors = [_LINE_COLORS[i % len(_LINE_COLORS)] for i in range(len(source_names))]

    fig, ax = plt.subplots(figsize=(14, 7), facecolor=_BG_PRIMARY)
    ax.set_facecolor(_BG_PRIMARY)

    # Remove decorative spines; keep bottom and left in border color
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(_BORDER_COLOR)
    ax.spines['bottom'].set_color(_BORDER_COLOR)
    ax.tick_params(colors=_TEXT_PRIMARY, which='both')

    # Plot each source line
    lines = []
    for i, src in enumerate(source_names):
        y = [monthly[src].get(m, 0) for m in all_months]
        ax.plot(
            x_pos, y,
            color=colors[i],
            linewidth=2,
            marker='o',
            markersize=4,
            alpha=0.9,
            label=f'{src} ({source_totals[src]:,})',
        )
        lines.append((src, y, colors[i]))

    # Right-edge annotations anchored to the last COMPLETE month so a partial
    # current month doesn't collapse all labels to near zero.
    ref_idx = -2 if len(all_months) >= 2 else -1
    y_max = max(v for src in source_names for v in monthly[src].values()) or 30
    min_gap = max(1.5, y_max * 0.05)

    annot_data = [(src, y[x_last], y[ref_idx], color) for src, y, color in lines]
    sorted_annot = sorted(annot_data, key=lambda t: t[2])
    nudged_y = _nudge_labels([ref_y for _, _, ref_y, _ in sorted_annot], min_gap=min_gap)

    # Extend x-axis to leave a margin for the labels
    ax.set_xlim(-0.5, x_last + 2.2)

    for (src, last_y, ref_y, color), ny in zip(sorted_annot, nudged_y):
        ax.annotate(
            src,
            xy=(x_last, last_y),
            xytext=(x_last + 0.35, ny),
            textcoords='data',
            color=color,
            fontsize=8,
            va='center',
            fontweight='bold',
            annotation_clip=False,
        )

    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels, fontsize=8, color=_TEXT_PRIMARY)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.yaxis.grid(True, color=_BORDER_COLOR, alpha=0.35, linestyle='--', linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_ylabel('Links per month', fontsize=10, color=_TEXT_PRIMARY)
    ax.yaxis.set_tick_params(labelcolor=_TEXT_PRIMARY)
    ax.set_title(
        f'Top {top_n} News Sources — Last {lookback_months} Months',
        fontsize=13,
        fontweight='600',
        color=_TEXT_SECONDARY,
        pad=12,
    )

    legend = ax.legend(
        bbox_to_anchor=(1.01, 1),
        loc='upper left',
        fontsize=8,
        framealpha=1.0,
        facecolor=_BG_SECONDARY,
        edgecolor=_BORDER_COLOR,
        title='Source (total links)',
        title_fontsize=8,
    )
    legend.get_title().set_color(_TEXT_SECONDARY)
    for text in legend.get_texts():
        text.set_color(_TEXT_PRIMARY)

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    fig.savefig(output_path, format='svg', bbox_inches='tight', facecolor=_BG_PRIMARY)
    plt.close(fig)

    print(f'  ✓ Saved: {output_path}')


def main():
    parser = argparse.ArgumentParser(
        description='Generate horse race SVG chart of top news sources over time',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run source_race_plot.py              # Generate (skip if already done this month)
  uv run source_race_plot.py --force      # Force regeneration
  uv run source_race_plot.py --top 15     # Show top 15 sources
        """,
    )
    parser.add_argument('--db', default=DEFAULT_DB)
    parser.add_argument('--output', default=DEFAULT_OUTPUT)
    parser.add_argument('--top', type=int, default=DEFAULT_TOP_N, dest='top_n')
    parser.add_argument('--lookback', type=int, default=DEFAULT_LOOKBACK)
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()

    if not os.path.exists(args.db):
        print(f'Error: database not found: {args.db}')
        sys.exit(1)

    if not args.force and not should_regenerate():
        print('Plot already generated this month. Use --force to regenerate.')
        sys.exit(0)

    generate_race_plot(
        db_path=args.db,
        output_path=args.output,
        top_n=args.top_n,
        lookback_months=args.lookback,
    )
    mark_as_run()


if __name__ == '__main__':
    main()
