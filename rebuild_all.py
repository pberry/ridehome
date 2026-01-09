#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrator script to rebuild all generated markdown files from database.
Calls all generator scripts in correct order.
"""
import argparse
import sys
from pathlib import Path
from generate_year_pages import generate_all_year_pages
from generate_category_pages import generate_all_category_pages
from year_wrapped import generate_wrapped_report, generate_markdown_report
from generate_index import generate_index_content, write_index
from datetime import datetime
from zoneinfo import ZoneInfo

PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


def rebuild_year_pages(db_path, docs_dir, force):
    """
    Rebuild year pages (all-links-YYYY.md, longreads-YYYY.md).

    Returns:
        dict: Statistics about what was generated
    """
    print("=" * 60)
    print("GENERATING YEAR PAGES")
    print("=" * 60)

    stats = generate_all_year_pages(db_path, docs_dir, force)
    return stats


def rebuild_category_pages(db_path, docs_dir, force):
    """
    Rebuild category pages.

    Returns:
        int: Number of categories generated
    """
    print("\n" + "=" * 60)
    print("GENERATING CATEGORY PAGES")
    print("=" * 60)

    categories_output = Path(docs_dir) / 'categories'
    categories_output.mkdir(exist_ok=True)

    # generate_all_category_pages doesn't have a return value, so call it directly
    generate_all_category_pages(db_path, str(categories_output))

    return 0  # We don't have stats from this generator


def rebuild_wrapped_reports(docs_dir, force):
    """
    Rebuild wrapped reports for all available years.

    Note: We only regenerate if force=True, otherwise wrapped reports
    are typically only generated once per year.

    Returns:
        int: Number of wrapped reports generated
    """
    print("\n" + "=" * 60)
    print("GENERATING WRAPPED REPORTS")
    print("=" * 60)

    if not force:
        print("  Skipping wrapped reports (use --force to regenerate)")
        print("  Wrapped reports are typically generated once per year")
        return 0

    # Find existing wrapped files to know which years to regenerate
    docs_path = Path(docs_dir)
    wrapped_years = []

    for file in docs_path.glob('*-wrapped.md'):
        year = file.stem.replace('-wrapped', '')
        if year.isdigit():
            wrapped_years.append(int(year))

    wrapped_years.sort(reverse=True)

    if not wrapped_years:
        print("  No existing wrapped files found")
        return 0

    count = 0
    for year in wrapped_years:
        print(f"\n  Generating {year} wrapped report...")
        try:
            stats = generate_wrapped_report(year)
            md_content = generate_markdown_report(stats)
            output_file = docs_path / f'{year}-wrapped.md'

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(md_content)

            print(f"  ✓ {year} wrapped: regenerated")
            count += 1
        except Exception as e:
            print(f"  ⚠ {year} wrapped: failed ({e})")

    return count


def rebuild_index(db_path, docs_dir):
    """
    Rebuild index.md homepage.

    Returns:
        bool: True if successful
    """
    print("\n" + "=" * 60)
    print("GENERATING INDEX.MD")
    print("=" * 60)

    try:
        content = generate_index_content(db_path, docs_dir)
        index_path = str(Path(docs_dir) / 'index.md')
        write_index(content, index_path)
        print(f"  ✓ index.md: regenerated")
        return True
    except Exception as e:
        print(f"  ⚠ index.md: failed ({e})")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Rebuild all generated markdown files from database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./rebuild_all.py                 # Incremental rebuild (skip unchanged files)
  ./rebuild_all.py --force         # Force regeneration of all files
  ./rebuild_all.py --db custom.db  # Use custom database
        """
    )

    parser.add_argument('--db', default='ridehome.db',
                        help='Database path (default: ridehome.db)')
    parser.add_argument('--docs', default='docs',
                        help='Docs directory (default: docs)')
    parser.add_argument('--force', action='store_true',
                        help='Force regeneration of all files (skip hash checks)')

    args = parser.parse_args()

    # Validate database exists
    if not Path(args.db).exists():
        print(f"❌ Error: Database not found: {args.db}")
        sys.exit(1)

    # Validate docs directory exists
    if not Path(args.docs).exists():
        print(f"❌ Error: Docs directory not found: {args.docs}")
        sys.exit(1)

    print("REBUILDING ALL MARKDOWN FILES")
    print(f"Database: {args.db}")
    print(f"Output: {args.docs}")
    print(f"Mode: {'FORCE (regenerate all)' if args.force else 'INCREMENTAL (skip unchanged)'}")
    print()

    # Track statistics
    total_generated = 0
    total_skipped = 0

    # 1. Generate year pages
    year_stats = rebuild_year_pages(args.db, args.docs, args.force)
    total_generated += year_stats['written']
    total_skipped += year_stats['skipped']

    # 2. Generate category pages
    rebuild_category_pages(args.db, args.docs, args.force)

    # 3. Generate wrapped reports (only if --force)
    wrapped_count = rebuild_wrapped_reports(args.docs, args.force)
    total_generated += wrapped_count

    # 4. Generate index.md (always regenerate)
    rebuild_index(args.db, args.docs)
    total_generated += 1

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Generated: {total_generated} files")
    if total_skipped > 0:
        print(f"  Skipped (unchanged): {total_skipped} files")
    print(f"\n✅ Rebuild complete")


if __name__ == '__main__':
    main()
