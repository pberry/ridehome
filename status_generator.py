#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate status section for homepage showing:
- Last run date/time
- Total links archived (showlinks and longreads)
- Top 3 sources from last 6 months
- Top 3 topics from last 6 months
"""
import sqlite3
import re
from datetime import datetime, timedelta
from collections import Counter


# Topic categorization based on keywords in titles
# Order matters: more specific categories first to avoid false matches
TOPIC_KEYWORDS = {
    # Specific tech categories (most specific first)
    'Regulation/Policy': [
        'regulation', 'antitrust', 'ftc', 'sec', 'doj', 'congress', 'senate',
        'lawsuit', 'legal', 'bill', 'legislation', 'policy', 'ban', 'law'
    ],
    'Security/Privacy': [
        'breach', 'hack', 'security', 'privacy', 'encryption', 'vulnerability',
        'cyberattack', 'ransomware', 'malware', 'data breach'
    ],
    'Crypto/Blockchain': [
        'bitcoin', 'crypto', 'blockchain', 'ethereum', 'nft', 'web3', 'defi',
        'coinbase', 'binance', 'solana', 'cryptocurrency'
    ],
    'Gaming': [
        'game', 'gaming', 'riot', 'league of legends', 'xbox', 'playstation',
        'nintendo', 'steam', 'epic games', 'esports', 'twitch'
    ],
    'Hardware/Chips': [
        'chip', 'tpu', 'nvidia', 'amd', 'intel', 'processor', 'gpu', 'cpu',
        'semiconductor', 'tsmc', 'qualcomm', 'arm'
    ],
    'AI/Machine Learning': [
        'ai', 'chatgpt', 'openai', 'gemini', 'claude', 'llm', 'machine learning',
        'neural', 'gpt', 'anthropic', 'midjourney', 'stable diffusion', 'deepmind',
        'copilot', 'artificial intelligence'
    ],
    'Automotive/Mobility': [
        'tesla', 'waymo', 'ev', 'electric vehicle', 'autonomous', 'self-driving',
        'uber', 'lyft', 'cruise', 'rivian', 'ford', 'gm'
    ],
    'Streaming/Entertainment': [
        'netflix', 'spotify', 'youtube', 'streaming', 'disney', 'hulu',
        'paramount', 'warner', 'hbo', 'music', 'video'
    ],
    'E-commerce/Retail': [
        'amazon', 'instacart', 'shopify', 'retail', 'walmart', 'target',
        'e-commerce', 'ecommerce', 'shopping'
    ],
    'Social Media': [
        'facebook', 'meta', 'twitter', 'tiktok', 'instagram', 'snapchat',
        'social media', 'threads', 'bluesky', 'mastodon'
    ],
    'Cloud/Enterprise': [
        'aws', 'azure', 'google cloud', 'enterprise', 'saas', 'salesforce',
        'oracle', 'sap', 'workday', 'cloud computing'
    ],
}


def categorize_topic(title):
    """
    Categorize a link title into a topic based on keyword matching.
    Returns the first matching topic or 'Other Tech News'.
    """
    if not title:
        return 'Other Tech News'

    title_lower = title.lower()

    # Use word boundaries to avoid partial matches
    # For multi-word keywords, check as-is
    # For single words, use word boundaries
    for topic, keywords in TOPIC_KEYWORDS.items():
        for keyword in keywords:
            keyword_lower = keyword.lower()

            # Multi-word keywords: exact substring match
            if ' ' in keyword_lower:
                if keyword_lower in title_lower:
                    return topic
            else:
                # Single word: use word boundary matching
                # Check if keyword appears as whole word
                pattern = r'\b' + re.escape(keyword_lower) + r'\b'
                if re.search(pattern, title_lower):
                    return topic

    return 'Other Tech News'


def get_status_data(db_path='ridehome.db'):
    """
    Query database and generate status statistics.

    Returns:
        dict with keys: last_run, total_showlinks, total_longreads,
        top_sources, top_topics
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get total counts by type
    cursor.execute("""
        SELECT link_type, COUNT(*) as count
        FROM links
        GROUP BY link_type
    """)
    counts = {row[0]: row[1] for row in cursor.fetchall()}

    # Get top 3 sources from last 6 months
    six_months_ago = datetime.now() - timedelta(days=180)
    six_months_ago_unix = int(six_months_ago.timestamp())

    cursor.execute("""
        SELECT source, COUNT(*) as count
        FROM links
        WHERE date_unix >= ? AND source IS NOT NULL
        GROUP BY source
        ORDER BY count DESC
        LIMIT 3
    """, (six_months_ago_unix,))
    top_sources = [(row[0], row[1]) for row in cursor.fetchall()]

    # Get all titles from last 6 months for topic categorization
    cursor.execute("""
        SELECT title
        FROM links
        WHERE date_unix >= ?
    """, (six_months_ago_unix,))

    titles = [row[0] for row in cursor.fetchall()]

    # Categorize topics
    topic_counts = Counter()
    for title in titles:
        topic = categorize_topic(title)
        if topic:
            topic_counts[topic] += 1

    top_topics = topic_counts.most_common(3)

    # Get last run time (most recent created_at in database)
    cursor.execute("SELECT MAX(created_at) FROM links")
    last_run_str = cursor.fetchone()[0]

    conn.close()

    # Parse last run time
    if last_run_str:
        try:
            # SQLite CURRENT_TIMESTAMP format: "YYYY-MM-DD HH:MM:SS"
            last_run = datetime.strptime(last_run_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            # Fallback if format is different
            last_run = datetime.now()
    else:
        last_run = datetime.now()

    return {
        'last_run': last_run,
        'total_showlinks': counts.get('showlink', 0),
        'total_longreads': counts.get('longread', 0),
        'top_sources': top_sources,
        'top_topics': top_topics
    }


def format_status_section(status_data):
    """
    Format status data as HTML with 3-column responsive grid layout.

    Args:
        status_data: dict from get_status_data()

    Returns:
        str: HTML formatted status section with semantic markup and accessibility
    """
    last_run = status_data['last_run'].strftime("%B %d, %Y at %I:%M %p")

    # Build source list
    sources_html = ""
    for i, (source, count) in enumerate(status_data['top_sources'], 1):
        sources_html += f'        <li><span class="stat-label">{source}</span> <span class="stat-value">({count:,} links)</span></li>\n'

    # Build topics list
    topics_html = ""
    for i, (topic, count) in enumerate(status_data['top_topics'], 1):
        topics_html += f'        <li><span class="stat-label">{topic}</span> <span class="stat-value">({count:,} links)</span></li>\n'

    status = f"""<section class="status-section" aria-labelledby="status-heading">
  <h2 id="status-heading">Current Status</h2>
  <p class="status-updated">Last Updated: <time datetime="{status_data['last_run'].isoformat()}">{last_run}</time></p>

  <div class="status-grid">
    <div class="status-card">
      <h3>Archive Size</h3>
      <ul class="status-list">
        <li><span class="stat-label">Show Links</span> <span class="stat-value stat-number">{status_data['total_showlinks']:,}</span></li>
        <li><span class="stat-label">Weekend Longreads</span> <span class="stat-value stat-number">{status_data['total_longreads']:,}</span></li>
      </ul>
    </div>

    <div class="status-card">
      <h3>Top Sources <span class="stat-period">(Last 6 Months)</span></h3>
      <ol class="status-list">
{sources_html}      </ol>
    </div>

    <div class="status-card">
      <h3>Top Topics <span class="stat-period">(Last 6 Months)</span></h3>
      <ol class="status-list">
{topics_html}      </ol>
    </div>
  </div>
</section>"""

    return status


def update_homepage(status_section, homepage_path='docs/index.md'):
    """
    Update homepage with new status section.
    Looks for <!-- STATUS_SECTION --> marker and replaces content between
    that marker and the next section or end.
    """
    with open(homepage_path, 'r', encoding='utf-8') as f:
        content = f.read()

    marker_start = '<!-- STATUS_SECTION -->'
    marker_end = '<!-- END_STATUS_SECTION -->'

    if marker_start not in content:
        raise ValueError(f"Marker '{marker_start}' not found in {homepage_path}")

    if marker_end not in content:
        raise ValueError(f"Marker '{marker_end}' not found in {homepage_path}")

    # Find marker positions
    start_pos = content.find(marker_start)
    end_pos = content.find(marker_end)

    if end_pos < start_pos:
        raise ValueError("End marker appears before start marker")

    # Replace content between markers
    before = content[:start_pos + len(marker_start)]
    after = content[end_pos:]

    updated_content = f"{before}\n\n{status_section}\n{after}"

    with open(homepage_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)


def main():
    """Generate and update homepage status section."""
    print("Generating status section...")

    status_data = get_status_data()
    status_section = format_status_section(status_data)

    print(status_section)
    print("\nUpdating homepage...")

    update_homepage(status_section)

    print("✓ Homepage updated successfully")


if __name__ == '__main__':
    main()
