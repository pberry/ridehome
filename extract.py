#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified RSS feed extractor for The Ride Home podcast.
Extracts show links and/or Friday longreads from feed and outputs to markdown files.
"""
import feedparser
import html2text
import time
import argparse
import os
from datetime import datetime
from html_parser import find_links_section, find_section
from file_updater import parse_top_date, find_new_entries, group_entries_by_year, infer_year_from_context


# Configuration for each extraction type
CONFIGS = {
	'showlinks': {
		'output_file_prefix': 'all-links',
		'header_template': 'showlinks-header.md',
		'deprecation_notice': "_This collection is no longe being updated. [The Ride Home](https://www.ridehome.info/podcast/techmeme-ride-home/) now has a proper web site and [RSS feed](https://feedly.com/i/subscription/feed/https://www.ridehome.info/rss/)._",
		'entry_type': 'showlinks',
		'no_content_message': 'entries',
		'include_podcast_title': True,
		'include_year_in_print': True,
		'header_spacing': '\n\n',  # Double newline after header in formatted output
	},
	'longreads': {
		'output_file_prefix': 'longreads',
		'header_template': 'longreads-header.md',
		'deprecation_notice': "_This collection is no longer being updated regularly. I still update it from time to time because this is the entire Long Read archive and I don't think everything transitioned to the site. [The Ride Home](https://www.ridehome.info/podcast/techmeme-ride-home/) now has a proper web site and [RSS feed](https://feedly.com/i/subscription/feed/https://www.ridehome.info/rss/)._",
		'entry_type': 'longreads',
		'no_content_message': 'longreads',
		'include_podcast_title': False,
		'include_year_in_print': False,
		'header_spacing': '\n',  # Single newline after header in formatted output
	}
}


def extract_html_content(post):
	"""Extract HTML content from feed entry. Returns HTML string or None."""
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
		return None

	return htmlContent.replace('\n', '')


def format_entry(post, config, include_year=None):
	"""
	Format a single feed entry as markdown for given type.
	Returns (header, content) or (None, None) if no matching content.
	"""
	# Determine whether to include year
	if include_year is None:
		include_year = config['include_year_in_print']

	# Format date
	if include_year:
		postPubTime = time.strftime("%A, %B %d %Y", post.published_parsed)
	else:
		postPubTime = time.strftime("%A, %B %d", post.published_parsed)

	# Build header
	if config['include_podcast_title']:
		podTitle = ""
		podTitleArray = post.title.split(' - ')
		if len(podTitleArray) > 1:
			podTitle = podTitleArray[1]
		else:
			podTitle = podTitleArray[0]
		header = f"**{postPubTime} - {podTitle}**"
	else:
		header = f"**{postPubTime}**"

	# Extract HTML content
	cleanPost = extract_html_content(post)
	if not cleanPost:
		return (None, None)

	# Find relevant section based on type
	if config['entry_type'] == 'showlinks':
		content_ul = find_links_section(cleanPost)
	elif config['entry_type'] == 'longreads':
		content_ul = find_section(cleanPost, pattern="Weekend Longreads|Longreads Suggestions")
	else:
		return (None, None)

	if content_ul:
		content = html2text.html2text(str(content_ul))
		return (header, content)
	else:
		return (None, None)


def print_mode(feed_entries, config):
	"""Print all entries to stdout"""
	for post in feed_entries:
		header, content = format_entry(post, config)
		if header and content:
			if config['entry_type'] == 'showlinks':
				print(f"\n{header}\n")
			else:
				print(header)
			print(content)
		elif config['entry_type'] == 'showlinks':
			# Only showlinks prints "no links" message
			postPubTime = time.strftime("%A, %B %d %Y", post.published_parsed)
			print(f"\n**{postPubTime}**")
			print("No show links for this episode ¯\\_(ツ)_/¯\n")


def update_mode(feed_entries, config):
	"""Update mode: detect new entries and update markdown file(s)"""
	if not feed_entries:
		print("No entries in feed")
		return

	# Determine current year file path
	latest_year = feed_entries[0].published_parsed.tm_year
	file_path = f"docs/{config['output_file_prefix']}-{latest_year}.md"

	# Parse top date from existing file (with year inference for longreads)
	if config['entry_type'] == 'longreads':
		year_context = infer_year_from_context(file_path)
		top_date = parse_top_date(file_path, entry_type=config['entry_type'], year_context=year_context)
	else:
		top_date = parse_top_date(file_path, entry_type=config['entry_type'])

	if top_date is None and os.path.exists(file_path):
		print(f"Error: No AUTO-GENERATED marker found in {file_path}")
		print("Please add '<!-- AUTO-GENERATED CONTENT BELOW -->' marker to the file.")
		return

	# Find new entries
	new_entries = find_new_entries(feed_entries, top_date)

	if not new_entries:
		print(f"No new entries found for {config['entry_type']}")
		return

	# Group new entries by year
	entries_by_year = group_entries_by_year(new_entries)

	# Format entries for each year (always include year in update mode)
	all_formatted = {}  # year -> list of (header, content) tuples
	total_count = 0

	for year, year_entries in sorted(entries_by_year.items(), reverse=True):
		formatted = []
		for post in year_entries:
			header, content = format_entry(post, config, include_year=True)
			if header and content:
				formatted.append((header, content))
		if formatted:
			all_formatted[year] = formatted
			total_count += len(formatted)

	if not all_formatted:
		print(f"No new {config['no_content_message']} found")
		return

	# Show prompt
	if len(all_formatted) == 1:
		# Single year
		year = list(all_formatted.keys())[0]
		file_path = f"docs/{config['output_file_prefix']}-{year}.md"
		print(f"Found {total_count} new {config['no_content_message']} for {year}:")
		for header, _ in all_formatted[year][:3]:
			print(f"  - {header}")
		if len(all_formatted[year]) > 3:
			print(f"  ... and {len(all_formatted[year]) - 3} more")
		response = input(f"\nAdd them to {file_path}? [y/N] ").strip().lower()
	else:
		# Multiple years
		print(f"Found {config['no_content_message']} for multiple years:")
		for year in sorted(all_formatted.keys(), reverse=True):
			count = len(all_formatted[year])
			print(f"  - {year}: {count} {config['no_content_message']}")
		response = input(f"\nUpdate all files? [y/N] ").strip().lower()

	if response != 'y':
		print("Cancelled")
		return

	# Insert entries for each year
	for year, formatted_entries in all_formatted.items():
		year_file_path = f"docs/{config['output_file_prefix']}-{year}.md"

		# Parse year-specific top date
		if config['entry_type'] == 'longreads':
			year_context = infer_year_from_context(year_file_path)
			year_top_date = parse_top_date(year_file_path, entry_type=config['entry_type'], year_context=year_context)
		else:
			year_top_date = parse_top_date(year_file_path, entry_type=config['entry_type'])

		create_new = (year_top_date is None and not os.path.exists(year_file_path))

		insert_entries(year_file_path, formatted_entries, config, create_if_missing=create_new)
		print(f"✓ Added {len(formatted_entries)} {config['no_content_message']} to {year_file_path}")


def insert_entries(file_path, formatted_entries, config, create_if_missing=False):
	"""Insert formatted entries above the AUTO-GENERATED marker"""
	if create_if_missing and not os.path.exists(file_path):
		# Create new file with header
		header = """{% include_relative _includes/""" + config['header_template'] + """ %}

""" + config['deprecation_notice'] + """

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

	# Format new entries as markdown (use config's header spacing)
	new_content = ""
	for header, entry_content in formatted_entries:
		new_content += f"{header}{config['header_spacing']}{entry_content}\n\n"

	# Reconstruct file: before marker + marker + new content + after marker
	updated_content = before_marker + marker + "\n\n" + new_content + after_marker.lstrip('\n')

	# Write back
	with open(file_path, 'w', encoding='utf-8') as f:
		f.write(updated_content)


def process_type(feed_entries, extract_type, print_only=False):
	"""Process a single extraction type"""
	if extract_type not in CONFIGS:
		print(f"Error: Unknown type '{extract_type}'")
		return False

	config = CONFIGS[extract_type]

	if print_only:
		print_mode(feed_entries, config)
	else:
		update_mode(feed_entries, config)

	return True


if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		description='Extract content from The Ride Home RSS feed',
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog="""
Examples:
  ./extract.py                           # Update showlinks (default)
  ./extract.py --type longreads          # Update longreads only
  ./extract.py --type all                # Update both showlinks and longreads
  ./extract.py --print                   # Print showlinks to stdout
  ./extract.py --type longreads --print  # Print longreads to stdout
		"""
	)
	parser.add_argument(
		'--type',
		choices=['showlinks', 'longreads', 'all'],
		default='showlinks',
		help='Type of content to extract (default: showlinks)'
	)
	parser.add_argument(
		'--print',
		action='store_true',
		help='Print to stdout instead of updating files'
	)
	args = parser.parse_args()

	# Parse RSS feed
	feedUrl = 'https://feeds.megaphone.fm/ridehome'
	rhfeed = feedparser.parse(feedUrl)

	# Process based on type
	if args.type == 'all':
		if args.print:
			print("Error: --print mode not supported with --type all")
			print("Use --type showlinks --print or --type longreads --print")
			exit(1)

		print("=== Processing showlinks ===")
		process_type(rhfeed.entries, 'showlinks', print_only=False)
		print("\n=== Processing longreads ===")
		process_type(rhfeed.entries, 'longreads', print_only=False)
	else:
		process_type(rhfeed.entries, args.type, print_only=args.print)
