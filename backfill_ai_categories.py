#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backfill AI categorization for all links in the database.

This script:
1. Finds all links without AI categorization
2. Processes them in batches using Claude API
3. Stores the results in the database

Usage:
    # Dry run (show what would be done, no API calls)
    python3 backfill_ai_categories.py --dry-run

    # Process first 100 titles (test run)
    python3 backfill_ai_categories.py --limit 100

    # Process all uncategorized titles
    python3 backfill_ai_categories.py

    # Use Sonnet model instead of Haiku (higher quality, 3x cost)
    python3 backfill_ai_categories.py --model sonnet

Cost estimate:
    - Haiku (default): ~$1.50 for all 13,833 titles
    - Sonnet: ~$4.50 for all 13,833 titles
"""
import os
import sys
import sqlite3
import argparse
from datetime import datetime
from claude_categorizer import categorize_with_retry, normalize_title


# Model configurations
MODELS = {
    'haiku': 'claude-3-5-haiku-20241022',
    'sonnet': 'claude-3-5-sonnet-20241022'
}


def get_uncategorized_links(db_path='ridehome.db', limit=None):
    """
    Get all links that don't have AI categorization yet.

    Args:
        db_path: Path to database
        limit: Optional limit on number of results

    Returns:
        list of tuples: (id, title)
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = """
        SELECT id, title
        FROM links
        WHERE ai_category IS NULL
          AND title IS NOT NULL
          AND title != ''
        ORDER BY date_unix DESC
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()

    return results


def save_categorizations(db_path, categorizations, model_name):
    """
    Save AI categorizations to database.

    Args:
        db_path: Path to database
        categorizations: dict mapping link_id to category
        model_name: Name of Claude model used

    Returns:
        int: Number of rows updated
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    updated = 0
    for link_id, category in categorizations.items():
        cursor.execute("""
            UPDATE links
            SET ai_category = ?,
                ai_categorized_at = CURRENT_TIMESTAMP,
                ai_model = ?
            WHERE id = ?
        """, (category, model_name, link_id))
        updated += cursor.rowcount

    conn.commit()
    conn.close()

    return updated


def estimate_cost(num_titles, model='haiku'):
    """
    Estimate the cost of categorizing titles.

    Args:
        num_titles: Number of titles to categorize
        model: 'haiku' or 'sonnet'

    Returns:
        float: Estimated cost in USD
    """
    # Average tokens per title: ~9
    # System prompt: ~90 tokens
    # User prompt overhead: ~20 tokens per batch

    # For 100 titles:
    # Input: 90 + 20 + (100 * 9) = ~1,010 tokens
    # Output: ~1,000 tokens (10 tokens per categorization)

    avg_input_per_100 = 1010
    avg_output_per_100 = 1000

    batches = (num_titles + 99) // 100  # Round up

    total_input = batches * avg_input_per_100
    total_output = batches * avg_output_per_100

    # Pricing per million tokens
    if model == 'haiku':
        input_price = 1.00 / 1_000_000
        output_price = 5.00 / 1_000_000
    else:  # sonnet
        input_price = 3.00 / 1_000_000
        output_price = 15.00 / 1_000_000

    cost = (total_input * input_price) + (total_output * output_price)
    return cost


def backfill_categories(batch_size=100, limit=None, model='haiku',
                       dry_run=False, db_path='ridehome.db'):
    """
    Main backfill function.

    Args:
        batch_size: Number of titles to process per API call
        limit: Optional limit on total titles to process
        model: 'haiku' or 'sonnet'
        dry_run: If True, only show what would be done
        db_path: Path to database

    Returns:
        dict with statistics
    """
    # Check for API key
    if not dry_run and not os.environ.get('ANTHROPIC_API_KEY'):
        print("❌ Error: ANTHROPIC_API_KEY not set")
        print("   Set it in your .env file or environment")
        return None

    # Get uncategorized links
    print(f"📊 Finding uncategorized links...")
    links = get_uncategorized_links(db_path, limit)

    if not links:
        print("✓ All links are already categorized!")
        return {'total': 0, 'processed': 0, 'cost': 0.0}

    print(f"   Found {len(links):,} links to categorize")

    # Estimate cost
    model_name = MODELS[model]
    estimated_cost = estimate_cost(len(links), model)
    print(f"\n💰 Cost Estimate:")
    print(f"   Model: {model_name}")
    print(f"   Titles: {len(links):,}")
    print(f"   Batches: {(len(links) + batch_size - 1) // batch_size}")
    print(f"   Estimated cost: ${estimated_cost:.2f}")

    if dry_run:
        print(f"\n🔍 DRY RUN - No API calls will be made")
        print(f"\nFirst 5 titles to be categorized:")
        for i, (link_id, title) in enumerate(links[:5], 1):
            print(f"   {i}. {title[:70]}")
        return {'total': len(links), 'processed': 0, 'cost': 0.0}

    # Confirm with user
    response = input(f"\nProceed with categorization? (y/N): ")
    if response.lower() != 'y':
        print("❌ Cancelled")
        return None

    # Process in batches
    print(f"\n🚀 Starting categorization...")
    print(f"   Batch size: {batch_size}")
    print(f"   Total batches: {(len(links) + batch_size - 1) // batch_size}")
    print()

    total_processed = 0
    failed_batches = []
    max_retries = 3

    for i in range(0, len(links), batch_size):
        batch = links[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(links) + batch_size - 1) // batch_size

        print(f"Batch {batch_num}/{total_batches}: Processing {len(batch)} titles...", end=" ")

        # Try processing batch with retries
        success = False
        last_error = None

        for attempt in range(max_retries):
            try:
                # Extract titles and IDs
                batch_titles = [title for link_id, title in batch]
                batch_ids = [link_id for link_id, title in batch]

                # Get categories from Claude (with automatic retry on invalid categories)
                results = categorize_with_retry(
                    batch_titles,
                    model=model_name
                )

                # Prepare categorizations with link IDs
                categorizations = {}
                for link_id, title in zip(batch_ids, batch_titles):
                    category = results.get(title, 'Other Tech News')
                    categorizations[link_id] = category

                # Save to database
                updated = save_categorizations(db_path, categorizations, model_name)

                total_processed += updated
                print(f"✓ Saved {updated} categorizations")
                success = True
                break  # Success, exit retry loop

            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    print(f"⚠ Attempt {attempt + 1} failed, retrying...", end=" ")
                else:
                    print(f"❌ Failed after {max_retries} attempts: {e}")

        if not success:
            failed_batches.append((batch_num, str(last_error)))
            # Continue with next batch instead of stopping

    # Summary
    print(f"\n" + "=" * 60)
    print(f"Backfill Complete")
    print(f"=" * 60)
    print(f"Total processed: {total_processed:,} links")
    print(f"Estimated cost: ${estimated_cost:.2f}")

    if failed_batches:
        print(f"\n⚠️  Failed batches: {len(failed_batches)}")
        for batch_num, error in failed_batches:
            print(f"   Batch {batch_num}: {error}")
        print(f"\nYou can re-run this script to process failed batches")

    return {
        'total': len(links),
        'processed': total_processed,
        'failed': len(failed_batches),
        'cost': estimated_cost
    }


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Backfill AI categorization for links',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--batch-size', type=int, default=100,
                       help='Number of titles per API call (default: 100)')
    parser.add_argument('--limit', type=int,
                       help='Limit total number of titles to process (for testing)')
    parser.add_argument('--model', choices=['haiku', 'sonnet'], default='haiku',
                       help='Claude model to use (default: haiku)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making API calls')
    parser.add_argument('--db', default='ridehome.db',
                       help='Path to database file (default: ridehome.db)')

    args = parser.parse_args()

    print("=" * 60)
    print("Backfill AI Categorization")
    print("=" * 60)
    print()

    result = backfill_categories(
        batch_size=args.batch_size,
        limit=args.limit,
        model=args.model,
        dry_run=args.dry_run,
        db_path=args.db
    )

    if result is None:
        sys.exit(1)

    if result['processed'] > 0:
        print(f"\n✓ Successfully categorized {result['processed']:,} links")
        sys.exit(0)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
