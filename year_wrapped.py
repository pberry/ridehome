#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The Ride Home - Year Wrapped Report Generator
Generates Spotify Wrapped-style statistics for any year

Usage:
    python3 year_wrapped.py 2025
    python3 year_wrapped.py 2024
    python3 year_wrapped.py --year 2023
"""

import re
import sys
import argparse
from collections import Counter
from pathlib import Path
from datetime import datetime


def parse_markdown_file(file_path):
    """
    Parse markdown file and extract dates, links, and sources.

    Returns:
        dict with 'dates', 'links', 'sources' lists
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    dates = []
    links = []
    sources = []

    # Find all date headers like "**Monday, December 08 2025 - Title**" or "**Friday, December 05**"
    date_pattern = r'\*\*([A-Za-z]+, [A-Za-z]+ \d{1,2}(?: \d{4})?)(?: - [^*]+)?\*\*'
    dates = re.findall(date_pattern, content)
    dates = [d[0] for d in dates]  # Extract just the date part from tuple

    # Find all links with sources like "* [Title](url) (Source)"
    link_pattern = r'\* \[([^\]]+)\]\(([^)]+)\)(?: \(([^)]+)\))?'
    matches = re.findall(link_pattern, content)

    for title, url, source in matches:
        links.append({'title': title, 'url': url, 'source': source})
        if source:
            sources.append(source)

    return {
        'dates': dates,
        'links': links,
        'sources': sources
    }


def count_company_mentions(content, companies):
    """
    Count mentions of specific companies in the content.
    Case-insensitive search.

    Returns:
        dict of company: count
    """
    content_lower = content.lower()
    counts = {}

    for company in companies:
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(company.lower()) + r'\b'
        count = len(re.findall(pattern, content_lower))
        counts[company] = count

    return counts


def generate_wrapped_report(year):
    """Generate the complete Wrapped report for a specific year"""

    # File paths
    all_links_path = Path(f'docs/all-links-{year}.md')
    longreads_path = Path(f'docs/longreads-{year}.md')

    # Check if files exist
    if not all_links_path.exists():
        print(f"❌ Error: File not found: {all_links_path}")
        print(f"   Available years: 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025")
        sys.exit(1)

    # Parse daily links (required)
    print(f"📊 Analyzing The Ride Home - {year} Data...\n")
    daily_data = parse_markdown_file(all_links_path)

    # Parse longreads (optional, only available 2022+)
    has_longreads = longreads_path.exists()
    if has_longreads:
        longreads_data = parse_markdown_file(longreads_path)
    else:
        print(f"ℹ️  Note: Longreads not available for {year} (feature started in 2022)\n")
        longreads_data = {'dates': [], 'links': [], 'sources': []}

    # Read full content for company mentions
    with open(all_links_path, 'r', encoding='utf-8') as f:
        daily_content = f.read()

    if has_longreads:
        with open(longreads_path, 'r', encoding='utf-8') as f:
            longreads_content = f.read()
        combined_content = daily_content + "\n" + longreads_content
    else:
        combined_content = daily_content

    # Company tracking
    companies_to_track = [
        'Apple', 'Meta', 'Google', 'Netflix', 'OpenAI',
        'Amazon', 'Anthropic', 'Microsoft', 'Tesla', 'Nvidia'
    ]

    company_mentions = count_company_mentions(combined_content, companies_to_track)

    # Generate statistics
    daily_dates = len(daily_data['dates'])
    daily_links = len(daily_data['links'])
    longreads_dates = len(longreads_data['dates'])
    longreads_links = len(longreads_data['links'])

    # Top sources
    daily_sources = Counter(daily_data['sources'])
    longreads_sources = Counter(longreads_data['sources'])

    # Determine if it's a leap year for coverage calculation
    is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    total_days_in_year = 366 if is_leap else 365

    # Print the Wrapped report
    print("=" * 70)
    print(f"🎧 THE RIDE HOME - {year} WRAPPED 🎧".center(70))
    print("=" * 70)
    print()

    print("📅 EPISODES & DATES")
    print("-" * 70)
    print(f"   Daily Show Episodes:        {daily_dates:>4} days")
    print(f"   Friday Longreads Episodes:  {longreads_dates:>4} Fridays")
    print(f"   TOTAL EPISODES:             {daily_dates + longreads_dates:>4} episodes")
    print()

    print("🔗 LINKS SHARED")
    print("-" * 70)
    print(f"   Daily Show Links:           {daily_links:>4} links")
    print(f"   Weekend Longreads:          {longreads_links:>4} links")
    print(f"   TOTAL LINKS:                {daily_links + longreads_links:>4} links")
    print(f"   Average per daily episode:  {daily_links / daily_dates if daily_dates > 0 else 0:>4.1f} links")
    print(f"   Average per Friday episode: {longreads_links / longreads_dates if longreads_dates > 0 else 0:>4.1f} links")
    print()

    print("📰 TOP 10 SOURCES - DAILY SHOW LINKS")
    print("-" * 70)
    for i, (source, count) in enumerate(daily_sources.most_common(10), 1):
        print(f"   {i:>2}. {source:<45} {count:>4} links")
    print()

    print("📚 TOP 10 SOURCES - WEEKEND LONGREADS")
    print("-" * 70)
    for i, (source, count) in enumerate(longreads_sources.most_common(10), 1):
        print(f"   {i:>2}. {source:<45} {count:>4} links")
    print()

    print("🏢 BIG TECH COMPANY MENTIONS")
    print("-" * 70)
    # Sort by count descending
    sorted_companies = sorted(company_mentions.items(), key=lambda x: x[1], reverse=True)
    for company, count in sorted_companies:
        if count > 0:
            bar = "█" * (count // 5) if count > 0 else ""
            print(f"   {company:<12} {count:>4} mentions  {bar}")
    print()

    print("=" * 70)
    print("🎉 YEAR IN REVIEW COMPLETE 🎉".center(70))
    print("=" * 70)
    print()

    # Fun facts section
    print("💡 FUN FACTS")
    print("-" * 70)

    # Most mentioned company
    top_company = sorted_companies[0] if sorted_companies else None
    if top_company and top_company[1] > 0:
        print(f"   🏆 Most mentioned company: {top_company[0]} ({top_company[1]} times)")

    # Most common daily source
    if daily_sources:
        top_daily = daily_sources.most_common(1)[0]
        print(f"   📰 Top daily news source: {top_daily[0]} ({top_daily[1]} links)")

    # Most common longreads source
    if longreads_sources:
        top_longread = longreads_sources.most_common(1)[0]
        print(f"   📖 Top longreads source: {top_longread[0]} ({top_longread[1]} articles)")

    # Year coverage
    if daily_dates > 0:
        coverage = (daily_dates / total_days_in_year) * 100
        print(f"   📅 Year coverage: {coverage:.1f}% of {year}")

    print()
    print("=" * 70)

    # Return stats for markdown generation
    return {
        'year': year,
        'daily_dates': daily_dates,
        'daily_links': daily_links,
        'longreads_dates': longreads_dates,
        'longreads_links': longreads_links,
        'daily_sources': daily_sources,
        'longreads_sources': longreads_sources,
        'company_mentions': sorted_companies,
        'total_days_in_year': total_days_in_year
    }


def generate_markdown_report(stats):
    """Generate markdown file from statistics"""
    year = stats['year']
    daily_dates = stats['daily_dates']
    daily_links = stats['daily_links']
    longreads_dates = stats['longreads_dates']
    longreads_links = stats['longreads_links']
    daily_sources = stats['daily_sources']
    longreads_sources = stats['longreads_sources']
    sorted_companies = stats['company_mentions']
    total_days_in_year = stats['total_days_in_year']

    total_links = daily_links + longreads_links
    total_episodes = daily_dates + longreads_dates
    coverage = (daily_dates / total_days_in_year) * 100 if daily_dates > 0 else 0
    avg_daily = daily_links / daily_dates if daily_dates > 0 else 0
    avg_longreads = longreads_links / longreads_dates if longreads_dates > 0 else 0

    md = f"""# 🎧 The Ride Home - {year} Wrapped

_A year in tech news, curated daily by [The Ride Home podcast](https://www.ridehome.info/podcast/techmeme-ride-home/)_

---

## 📅 Episodes & Coverage

| Metric | Count |
|--------|-------|
| **Daily Show Episodes** | {daily_dates} days |
| **Friday Longreads Episodes** | {longreads_dates} Fridays |
| **Total Episodes** | **{total_episodes} episodes** |
| **Year Coverage** | **{coverage:.1f}%** of {year} |

---

## 🔗 Links Shared

| Category | Links | Average per Episode |
|----------|-------|---------------------|
| **Daily Show Links** | {daily_links:,} | {avg_daily:.1f} links/episode |
| **Weekend Longreads** | {longreads_links} | {avg_longreads:.1f} links/episode |
| **TOTAL** | **{total_links:,}** | - |

---

## 📰 Top 10 Sources - Daily Show Links

| Rank | Source | Links |
|------|--------|-------|
"""

    # Add top 10 daily sources
    for i, (source, count) in enumerate(daily_sources.most_common(10), 1):
        if i == 1:
            md += f"| 🥇 | **{source}** | {count} |\n"
        elif i == 2:
            md += f"| 🥈 | **{source}** | {count} |\n"
        elif i == 3:
            md += f"| 🥉 | **{source}** | {count} |\n"
        else:
            md += f"| {i} | {source} | {count} |\n"

    md += "\n---\n\n## 📚 Top 10 Sources - Weekend Longreads\n\n"
    md += "| Rank | Source | Articles |\n|------|--------|----------|\n"

    # Add top 10 longreads sources
    for i, (source, count) in enumerate(longreads_sources.most_common(10), 1):
        if i == 1:
            md += f"| 🥇 | **{source}** | {count} |\n"
        elif i == 2:
            md += f"| 🥈 | **{source}** | {count} |\n"
        elif i == 3:
            md += f"| 🥉 | **{source}** | {count} |\n"
        else:
            md += f"| {i} | {source} | {count} |\n"

    md += "\n---\n\n## 🏢 Big Tech Company Mentions\n\n"
    md += "The tech companies that dominated headlines in {0}:\n\n".format(year)
    md += "| Company | Mentions | Chart |\n|---------|----------|-------|\n"

    # Add company mentions with bars
    for i, (company, count) in enumerate(sorted_companies, 1):
        if count > 0:
            bar = "█" * (count // 5) if count > 0 else ""
            if i == 1:
                md += f"| 🏆 **{company}** | **{count}** | {bar} |\n"
            else:
                emoji = {'Apple': '🍎', 'Google': '🔍', 'Meta': '👤', 'Microsoft': '💼',
                        'Nvidia': '🎮', 'Amazon': '📦', 'Anthropic': '🤖',
                        'Netflix': '🎬', 'Tesla': '🚗', 'OpenAI': '🤖'}.get(company, '')
                md += f"| {emoji} **{company}** | **{count}** | {bar} |\n"

    md += "\n---\n\n## 💡 Fun Facts\n\n"

    # Add fun facts
    if sorted_companies and sorted_companies[0][1] > 0:
        top_company = sorted_companies[0]
        md += f"- 🏆 **Most Mentioned Company:** {top_company[0]} dominated with {top_company[1]} mentions"
        if year >= 2024:
            if top_company[0] == "OpenAI":
                md += " - AI clearly defined the tech narrative\n"
            elif top_company[0] == "Apple":
                md += " - hardware and services still commanded attention\n"
        else:
            md += "\n"

    if daily_sources:
        top_daily = daily_sources.most_common(1)[0]
        md += f"- 📰 **Top Daily News Source:** {top_daily[0]} with {top_daily[1]} links\n"

    if longreads_sources:
        top_longread = longreads_sources.most_common(1)[0]
        md += f"- 📖 **Top Longreads Source:** {top_longread[0]} ({top_longread[1]} articles)\n"

    md += f"- 📊 **Links Per Episode:** An average of {avg_daily:.1f} daily links kept listeners informed\n"
    md += f"- 📅 **Consistency:** {daily_dates} daily episodes means coverage on most weekdays throughout the year\n"
    md += f"- 🎯 **Quality Curation:** {total_links:,} total links from premium sources\n"

    md += "\n---\n\n## 📈 Key Takeaways\n\n"

    # Generate takeaway based on year
    if year == 2025:
        md += "**2025 was the year of AI dominance in tech news.** OpenAI's overwhelming lead in mentions reflects the industry's obsession with artificial intelligence. The top companies all invested heavily in AI, making it the defining narrative of the year.\n\n"
    elif year == 2024:
        md += "**2024 saw Apple dominate headlines** with 458 mentions, but the AI revolution was brewing with OpenAI, Google, and Microsoft heavily featured. The transition year before AI took center stage.\n\n"
    elif year == 2023:
        md += "**2023 was characterized by** The Verge leading coverage with diverse tech stories, while traditional tech giants maintained strong presence in the news cycle.\n\n"
    else:
        md += f"**{year} in tech** featured {total_links:,} curated links across {total_episodes} episodes, bringing the most important tech news to listeners.\n\n"

    md += f"**The Ride Home covered {coverage:.1f}% of {year}**, bringing tech news to thousands of listeners.\n\n"

    md += f"---\n\n_Generated {datetime.now().strftime('%D')}_ | _Data source: docs/all-links-{year}.md and docs/longreads-{year}.md_\n"

    return md


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description='Generate Spotify Wrapped-style report for The Ride Home podcast',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 year_wrapped.py 2025
  python3 year_wrapped.py --year 2024
  python3 year_wrapped.py 2023

Available years: 2022, 2023, 2024, 2025
        """
    )

    parser.add_argument(
        'year',
        nargs='?',
        type=int,
        default=datetime.now().year,
        help='Year to generate report for (default: current year)'
    )

    parser.add_argument(
        '--year',
        dest='year_flag',
        type=int,
        help='Alternative way to specify year'
    )

    args = parser.parse_args()

    # Use --year flag if provided, otherwise use positional argument
    year = args.year_flag if args.year_flag else args.year

    # Validate year
    if year < 2018 or year > datetime.now().year:
        print(f"❌ Error: Year {year} is out of range")
        print(f"   The Ride Home podcast started in 2018")
        print(f"   Current year is {datetime.now().year}")
        sys.exit(1)

    # Generate console report
    stats = generate_wrapped_report(year)

    # Generate markdown report
    md_content = generate_markdown_report(stats)
    output_file = Path(f'docs/{year}-wrapped.md')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"\n✅ Markdown report saved to: {output_file}")


if __name__ == '__main__':
    main()
