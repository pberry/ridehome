#!/usr/bin/env python3
"""
Database migration script to normalize source names.

Performs two operations:
1. Normalize existing sources (fix variations, typos, author attributions)
2. Fill NULL sources by parsing URLs

Generates detailed migration report showing before/after statistics.
"""

import sqlite3
from collections import Counter, defaultdict
from source_normalizer import normalize_source, extract_source_from_url


def export_statistics(cursor, title):
    """Export current database statistics."""
    stats = {}

    # Total links
    cursor.execute("SELECT COUNT(*) FROM links")
    stats['total_links'] = cursor.fetchone()[0]

    # Links with sources
    cursor.execute("SELECT COUNT(*) FROM links WHERE source IS NOT NULL")
    stats['with_source'] = cursor.fetchone()[0]

    # NULL sources
    stats['null_sources'] = stats['total_links'] - stats['with_source']

    # Distinct source values
    cursor.execute("SELECT COUNT(DISTINCT source) FROM links WHERE source IS NOT NULL")
    stats['distinct_sources'] = cursor.fetchone()[0]

    # Top sources
    cursor.execute("""
        SELECT source, COUNT(*) as count
        FROM links
        WHERE source IS NOT NULL
        GROUP BY source
        ORDER BY count DESC
        LIMIT 50
    """)
    stats['top_sources'] = cursor.fetchall()

    return stats


def normalize_existing_sources(conn):
    """Normalize all non-NULL sources in database."""
    cursor = conn.cursor()

    # Get all non-NULL sources
    cursor.execute("SELECT id, source FROM links WHERE source IS NOT NULL")
    links = cursor.fetchall()

    changes = defaultdict(list)
    unchanged_count = 0

    for link_id, old_source in links:
        new_source = normalize_source(old_source)

        if new_source != old_source:
            cursor.execute("UPDATE links SET source = ? WHERE id = ?", (new_source, link_id))
            changes[f"{old_source} → {new_source}"].append(link_id)
        else:
            unchanged_count += 1

    conn.commit()

    return {
        'processed': len(links),
        'changed': sum(len(ids) for ids in changes.values()),
        'unchanged': unchanged_count,
        'changes': changes
    }


def fill_null_sources(conn):
    """Fill NULL sources by parsing URLs."""
    cursor = conn.cursor()

    # Get all NULL sources
    cursor.execute("SELECT id, url FROM links WHERE source IS NULL")
    links = cursor.fetchall()

    fills = defaultdict(list)
    unknown_domains = defaultdict(list)

    for link_id, url in links:
        source = extract_source_from_url(url)

        if source:
            cursor.execute("UPDATE links SET source = ? WHERE id = ?", (source, link_id))
            fills[f"{url.split('/')[2] if '/' in url else url} → {source}"].append(link_id)
        else:
            # Extract domain for unknown domains report
            try:
                domain = url.split('/')[2] if '/' in url else url
                unknown_domains[domain].append(url)
            except:
                unknown_domains['<malformed>'].append(url)

    conn.commit()

    return {
        'processed': len(links),
        'filled': sum(len(ids) for ids in fills.values()),
        'unknown': sum(len(urls) for urls in unknown_domains.values()),
        'fills': fills,
        'unknown_domains': unknown_domains
    }


def generate_report(before_stats, normalize_results, fill_results, after_stats):
    """Generate comprehensive migration report."""
    report = []
    report.append("=" * 70)
    report.append("Source Normalization Migration Report")
    report.append("=" * 70)
    report.append("")

    # Pre-migration statistics
    report.append("Pre-Migration Statistics:")
    report.append("-" * 70)
    report.append(f"  Total links: {before_stats['total_links']:,}")
    report.append(f"  Links with sources: {before_stats['with_source']:,}")
    report.append(f"  NULL sources: {before_stats['null_sources']:,}")
    report.append(f"  Distinct source values: {before_stats['distinct_sources']:,}")
    report.append("")

    # Step 1: Normalize existing sources
    report.append("Step 1: Normalize Existing Sources")
    report.append("-" * 70)
    report.append(f"  Processed: {normalize_results['processed']:,} links with sources")
    report.append(f"  Changed: {normalize_results['changed']:,} links")
    report.append(f"  Unchanged: {normalize_results['unchanged']:,} links")
    report.append("")

    if normalize_results['changes']:
        report.append("  Sample changes (top 20):")
        sorted_changes = sorted(normalize_results['changes'].items(),
                              key=lambda x: len(x[1]), reverse=True)
        for change, ids in sorted_changes[:20]:
            report.append(f"    {change:50} ({len(ids)} occurrences)")
    report.append("")

    # Step 2: Fill NULL sources
    report.append("Step 2: Fill NULL Sources from URLs")
    report.append("-" * 70)
    report.append(f"  Processed: {fill_results['processed']:,} NULL sources")
    report.append(f"  Filled: {fill_results['filled']:,} sources")
    report.append(f"  Unknown domains: {fill_results['unknown']:,} sources")
    report.append("")

    if fill_results['fills']:
        report.append("  Sample fills (top 20):")
        sorted_fills = sorted(fill_results['fills'].items(),
                            key=lambda x: len(x[1]), reverse=True)
        for fill, ids in sorted_fills[:20]:
            report.append(f"    {fill:50} ({len(ids)} occurrences)")
    report.append("")

    if fill_results['unknown_domains']:
        report.append("  Unknown domains requiring manual review:")
        sorted_unknowns = sorted(fill_results['unknown_domains'].items(),
                                key=lambda x: len(x[1]), reverse=True)
        for domain, urls in sorted_unknowns:
            report.append(f"    {domain:40} ({len(urls)} occurrences)")
            # Show first 3 example URLs
            for url in urls[:3]:
                report.append(f"      {url}")
    report.append("")

    # Post-migration statistics
    report.append("Post-Migration Statistics:")
    report.append("-" * 70)
    report.append(f"  Total links: {after_stats['total_links']:,}")
    report.append(f"  Links with sources: {after_stats['with_source']:,}")
    report.append(f"  NULL sources: {after_stats['null_sources']:,}")
    report.append(f"  Distinct source values: {after_stats['distinct_sources']:,}")
    report.append("")

    # Before/after comparison
    report.append("Improvement Summary:")
    report.append("-" * 70)
    report.append(f"  NULL sources reduced: {before_stats['null_sources']:,} → {after_stats['null_sources']:,} "
                 f"({before_stats['null_sources'] - after_stats['null_sources']:,} filled)")
    report.append(f"  Distinct sources reduced: {before_stats['distinct_sources']:,} → {after_stats['distinct_sources']:,} "
                 f"({before_stats['distinct_sources'] - after_stats['distinct_sources']:,} consolidated)")
    report.append("")

    # Top 20 sources after migration
    report.append("Top 20 Sources (After Migration):")
    report.append("-" * 70)
    for i, (source, count) in enumerate(after_stats['top_sources'][:20], 1):
        report.append(f"  {i:2}. {source:40} {count:5,}")
    report.append("")

    report.append("=" * 70)
    report.append("Migration completed successfully!")
    report.append("=" * 70)

    return "\n".join(report)


def main():
    """Run migration."""
    db_path = 'ridehome.db'

    print("Connecting to database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Step 1: Export pre-migration statistics
    print("Exporting pre-migration statistics...")
    before_stats = export_statistics(cursor, "Before Migration")

    # Step 2: Normalize existing sources
    print("Normalizing existing sources...")
    normalize_results = normalize_existing_sources(conn)
    print(f"  Changed {normalize_results['changed']:,} sources")

    # Step 3: Fill NULL sources
    print("Filling NULL sources from URLs...")
    fill_results = fill_null_sources(conn)
    print(f"  Filled {fill_results['filled']:,} sources")
    print(f"  Unknown domains: {fill_results['unknown']:,}")

    # Step 4: Export post-migration statistics
    print("Exporting post-migration statistics...")
    after_stats = export_statistics(cursor, "After Migration")

    # Step 5: Generate report
    print("Generating migration report...")
    report = generate_report(before_stats, normalize_results, fill_results, after_stats)

    # Save report to file
    with open('migration_report.txt', 'w') as f:
        f.write(report)

    print("\n" + report)
    print(f"\nReport saved to: migration_report.txt")

    conn.close()


if __name__ == '__main__':
    main()
