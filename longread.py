#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import feedparser
import html2text
import time
import argparse
import os
from datetime import datetime
from html_parser import find_section
from file_updater import parse_top_date, find_new_entries, infer_year_from_context, group_entries_by_year


def format_entry(post, include_year=True):
	"""Format a single feed entry as markdown. Returns (header, content) or (None, None) if no longreads."""
	# NEW: Include year in date format for longreads
	if include_year:
		postPubTime = time.strftime("%A, %B %d %Y", post.published_parsed)
	else:
		# Old format for backward compatibility
		postPubTime = time.strftime("%A, %B %d", post.published_parsed)

	header = f"**{postPubTime}**"

	# Extract HTML content from content:encoded first, fall back to summary
	htmlContent = ""
	if hasattr(post, 'content') and len(post.content) > 0:
		# Look for HTML content (text/html type) first
		html_content = None
		for content_block in post.content:
			if content_block.get('type', '').lower() in ['text/html', 'html']:
				html_content = content_block.value
				break

		if html_content:
			htmlContent = html_content
		else:
			# Fall back to first content block
			htmlContent = post.content[0].value
	elif hasattr(post, 'summary'):
		htmlContent = post.summary
	else:
		return (None, None)

	cleanPost = htmlContent.replace('\n', '')

	# Try to find Longreads or Suggestions sections
	# Use specific pattern to avoid matching timestamps like "15:35 Longreads"
	longreads_ul = find_section(cleanPost, pattern="Weekend Longreads|Longreads Suggestions")

	if longreads_ul:
		content = html2text.html2text(str(longreads_ul))
		return (header, content)
	else:
		return (None, None)


def print_mode(feed_entries):
	"""Original behavior: print all entries to stdout (without year for backward compatibility)"""
	for post in feed_entries:
		header, content = format_entry(post, include_year=False)
		if header and content:
			print(header)
			print(content)


def update_mode(feed_entries):
	"""Update mode: detect new entries and update markdown file(s) with year-corrected format"""
	if not feed_entries:
		print("No entries in feed")
		return

	# Determine current year file path
	latest_year = feed_entries[0].published_parsed.tm_year
	file_path = f"docs/longreads-{latest_year}.md"

	# Parse top date from existing file
	year_context = infer_year_from_context(file_path)
	top_date = parse_top_date(file_path, entry_type='longreads', year_context=year_context)

	if top_date is None and os.path.exists(file_path):
		print(f"Error: No AUTO-GENERATED marker found in {file_path}")
		print("Please add '<!-- AUTO-GENERATED CONTENT BELOW -->' marker to the file.")
		return

	# Find new entries
	new_entries = find_new_entries(feed_entries, top_date)

	if not new_entries:
		print("No new entries found")
		return

	# Group new entries by year
	entries_by_year = group_entries_by_year(new_entries)

	# Format entries for each year (WITH year - new format)
	all_formatted = {}  # year -> list of (header, content) tuples
	total_count = 0

	for year, year_entries in sorted(entries_by_year.items(), reverse=True):
		formatted = []
		for post in year_entries:
			header, content = format_entry(post, include_year=True)
			if header and content:
				formatted.append((header, content))
		if formatted:
			all_formatted[year] = formatted
			total_count += len(formatted)

	if not all_formatted:
		print("No new longreads found")
		return

	# Show prompt
	if len(all_formatted) == 1:
		# Single year
		year = list(all_formatted.keys())[0]
		file_path = f"docs/longreads-{year}.md"
		print(f"Found {total_count} new longreads for {year}:")
		for header, _ in all_formatted[year][:3]:
			print(f"  - {header}")
		if len(all_formatted[year]) > 3:
			print(f"  ... and {len(all_formatted[year]) - 3} more")
		response = input(f"\nAdd them to {file_path}? [y/N] ").strip().lower()
	else:
		# Multiple years
		print(f"Found longreads for multiple years:")
		for year in sorted(all_formatted.keys(), reverse=True):
			count = len(all_formatted[year])
			print(f"  - {year}: {count} longreads")
		response = input(f"\nUpdate all files? [y/N] ").strip().lower()

	if response != 'y':
		print("Cancelled")
		return

	# Insert entries for each year
	for year, formatted_entries in all_formatted.items():
		year_file_path = f"docs/longreads-{year}.md"
		year_context = infer_year_from_context(year_file_path)
		year_top_date = parse_top_date(year_file_path, entry_type='longreads', year_context=year_context)
		create_new = (year_top_date is None and not os.path.exists(year_file_path))

		insert_entries(year_file_path, formatted_entries, create_if_missing=create_new)
		print(f"✓ Added {len(formatted_entries)} longreads to {year_file_path}")


def insert_entries(file_path, formatted_entries, create_if_missing=False):
	"""Insert formatted entries above the AUTO-GENERATED marker"""
	if create_if_missing and not os.path.exists(file_path):
		# Create new file with header
		header = """{% include_relative _includes/longreads-header.md %}

_This collection is no longer being updated regularly. I still update it from time to time because this is the entire Long Read archive and I don't think everything transitioned to the site. [The Ride Home](https://www.ridehome.info/podcast/techmeme-ride-home/) now has a proper web site and [RSS feed](https://feedly.com/i/subscription/feed/https://www.ridehome.info/rss/)._

 <!-- AUTO-GENERATED CONTENT BELOW -->

"""
		with open(file_path, 'w', encoding='utf-8') as f:
			f.write(header)

	# Read existing file
	with open(file_path, 'r', encoding='utf-8') as f:
		content = f.read()

	# Find marker
	marker = '<!-- AUTO-GENERATED CONTENT BELOW -->'
	if marker not in content:
		raise ValueError(f"Marker not found in {file_path}")

	# Split at marker
	before_marker, after_marker = content.split(marker, 1)

	# Format new entries as markdown
	new_content = ""
	for header, entry_content in formatted_entries:
		new_content += f"{header}\n{entry_content}\n\n"

	# Reconstruct file: before marker + marker + new content + after marker
	updated_content = before_marker + marker + "\n\n" + new_content + after_marker.lstrip('\n')

	# Write back
	with open(file_path, 'w', encoding='utf-8') as f:
		f.write(updated_content)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Extract longreads from The Ride Home RSS feed')
	parser.add_argument('--update', action='store_true', help='Update markdown file with new entries')
	args = parser.parse_args()

	rhfeed = feedparser.parse('https://feeds.megaphone.fm/ridehome')

	if args.update:
		update_mode(rhfeed.entries)
	else:
		print_mode(rhfeed.entries)
	