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
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
from html_parser import find_links_section, find_section
from db_schema import create_schema
from db_writer import insert_links
from status_generator import get_status_data, format_status_section, update_homepage
from claude_categorizer import categorize_with_retry
from source_normalizer import normalize_source
import sqlite3
import subprocess

# Pacific timezone for The Ride Home podcast
PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


# Configuration for each extraction type
CONFIGS = {
	'showlinks': {
		'output_file_prefix': 'all-links',
		'header_template': 'showlinks-header.md',
		'deprecation_notice': "[The Ride Home](https://www.ridehome.info/podcast/techmeme-ride-home/) now has a proper web site and [RSS feed](https://feedly.com/i/subscription/feed/https://www.ridehome.info/rss/).",
		'entry_type': 'showlinks',
		'no_content_message': 'entries',
		'include_podcast_title': True,
		'include_year_in_print': True,
		'header_spacing': '\n\n',  # Double newline after header in formatted output
	},
	'longreads': {
		'output_file_prefix': 'longreads',
		'header_template': 'longreads-header.md',
		'deprecation_notice': "[The Ride Home](https://www.ridehome.info/podcast/techmeme-ride-home/) now has a proper web site and [RSS feed](https://feedly.com/i/subscription/feed/https://www.ridehome.info/rss/).",
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


def extract_links_from_ul(ul_element, episode_date, episode_title):
	"""
	Extract structured link data from BeautifulSoup <ul> element.

	Args:
		ul_element: BeautifulSoup Tag object representing <ul>
		episode_date: datetime object for the episode
		episode_title: str, title of the podcast episode

	Returns:
		List of dicts with keys: date, title, url, source, episode_date, episode_title
	"""
	links = []

	if not ul_element:
		return links

	for li in ul_element.find_all('li'):
		# Find <a> tag
		a_tag = li.find('a')
		if not a_tag or not a_tag.get('href'):
			continue

		title = a_tag.get_text(strip=True)
		url = a_tag['href']

		# Extract source from text after link (usually in parentheses)
		# Pattern: <a>...</a> (Source) or <a>...</a>(Source)
		text_after_link = li.get_text()
		source = None

		# Try to find source in parentheses after the link title
		# Example: "Title text (Source)" or "Title text(Source)"
		pattern = r'\(([^\)]+)\)\s*$'
		match = re.search(pattern, text_after_link)
		if match:
			source = match.group(1).strip()
			# Normalize source to canonical form
			source = normalize_source(source)

		links.append({
			'date': episode_date,
			'title': title,
			'url': url,
			'source': source,
			'episode_date': episode_date,
			'episode_title': episode_title
		})

	return links


def format_entry(post, config, include_year=None):
	"""
	Format a single feed entry as markdown for given type.
	Returns (header, content) or (None, None) if no matching content.
	"""
	header, content, _ = format_entry_with_links(post, config, include_year)
	return (header, content)


def format_entry_with_links(post, config, include_year=None):
	"""
	Format a single feed entry as markdown AND extract structured links.
	Returns (header, content, links) where links is a list of dicts.
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
		return (None, None, [])

	# Find relevant section based on type
	if config['entry_type'] == 'showlinks':
		content_ul = find_links_section(cleanPost)
	elif config['entry_type'] == 'longreads':
		content_ul = find_section(cleanPost, pattern="Weekend Longreads|Longreads Suggestions")
	else:
		return (None, None, [])

	if content_ul:
		content = html2text.html2text(str(content_ul))

		# Extract episode title from post.title
		# Format: "The Ride Home - [Episode Title]"
		pod_title_array = post.title.split(' - ')
		if len(pod_title_array) > 1:
			episode_title = pod_title_array[1]
		else:
			episode_title = pod_title_array[0]

		# Extract structured links from the <ul> element
		# Convert UTC time from feed to Pacific time
		entry_time = time.struct_time(post.published_parsed)
		entry_dt_utc = datetime(*entry_time[:6], tzinfo=ZoneInfo("UTC"))
		episode_date = entry_dt_utc.astimezone(PACIFIC_TZ).replace(tzinfo=None)
		links = extract_links_from_ul(content_ul, episode_date, episode_title)

		return (header, content, links)
	else:
		return (None, None, [])


def get_latest_date_from_db(link_type, db_path='ridehome.db'):
	"""
	Get the most recent date for a given link type from database.

	Returns:
		datetime or None: Most recent date, or None if no data
	"""
	if not os.path.exists(db_path):
		return None

	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()

	cursor.execute("""
		SELECT MAX(date)
		FROM links
		WHERE link_type = ?
	""", (link_type,))

	result = cursor.fetchone()[0]
	conn.close()

	if result:
		return datetime.fromisoformat(result)

	return None


def find_new_entries(feed_entries, top_date=None, target_year=None):
	"""
	Filter feed entries to only those newer than top_date.

	Args:
		feed_entries: List of feedparser entry objects
		top_date: datetime object representing the most recent entry in DB
		target_year: Optional year to filter entries

	Returns:
		List of entries newer than top_date, in reverse chronological order
	"""
	def get_pacific_time(entry):
		"""Convert feed entry to Pacific timezone datetime"""
		entry_time = time.struct_time(entry['published_parsed'])
		entry_dt_utc = datetime(*entry_time[:6], tzinfo=ZoneInfo("UTC"))
		return entry_dt_utc.astimezone(PACIFIC_TZ)

	if top_date is None:
		if target_year is not None:
			# Filter to only entries from target_year
			filtered_entries = []
			for entry in feed_entries:
				entry_dt_pacific = get_pacific_time(entry)
				if entry_dt_pacific.year == target_year:
					filtered_entries.append(entry)

			filtered_entries.sort(key=get_pacific_time, reverse=True)
			return filtered_entries
		else:
			return feed_entries

	new_entries = []
	top_date_only = top_date.date()

	for entry in feed_entries:
		entry_dt_pacific = get_pacific_time(entry)
		entry_date_only = entry_dt_pacific.date()

		if entry_date_only > top_date_only:
			new_entries.append(entry)

	new_entries.sort(key=get_pacific_time, reverse=True)
	return new_entries


def group_entries_by_year(entries):
	"""
	Group feed entries by year.

	Returns:
		Dictionary mapping year (int) to list of entries for that year
	"""
	groups = {}
	for entry in entries:
		year = entry['published_parsed'].tm_year
		if year not in groups:
			groups[year] = []
		groups[year].append(entry)

	return groups


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


def update_mode(feed_entries, config, skip_db=False, yes=False):
	"""Update mode: detect new entries and update database, then regenerate markdown"""
	if not feed_entries:
		print("No entries in feed")
		return

	# Determine current year using Pacific timezone
	first_entry_time = time.struct_time(feed_entries[0].published_parsed)
	first_entry_utc = datetime(*first_entry_time[:6], tzinfo=ZoneInfo("UTC"))
	latest_year = first_entry_utc.astimezone(PACIFIC_TZ).year

	# Get latest date from database instead of markdown files
	link_type = 'showlink' if config['entry_type'] == 'showlinks' else 'longread'
	top_date = get_latest_date_from_db(link_type)

	# Find new entries
	new_entries = find_new_entries(feed_entries, top_date, target_year=latest_year)

	if not new_entries:
		print(f"No new entries found for {config['entry_type']}")
		return

	# Group new entries by year
	entries_by_year = group_entries_by_year(new_entries)

	# Format entries for each year (always include year in update mode)
	all_formatted = {}  # year -> list of (header, content) tuples
	all_db_links = []  # Collect all links for database insertion
	total_count = 0

	for year, year_entries in sorted(entries_by_year.items(), reverse=True):
		formatted = []
		for post in year_entries:
			header, content, links = format_entry_with_links(post, config, include_year=True)
			if header and content:
				formatted.append((header, content))
				all_db_links.extend(links)  # Collect links for DB
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
		if not yes:
			response = input(f"\nAdd them to {file_path}? [y/N] ").strip().lower()
			if response != 'y':
				print("Cancelled")
				return
	else:
		# Multiple years
		print(f"Found {config['no_content_message']} for multiple years:")
		for year in sorted(all_formatted.keys(), reverse=True):
			count = len(all_formatted[year])
			print(f"  - {year}: {count} {config['no_content_message']}")
		if not yes:
			response = input(f"\nUpdate all files? [y/N] ").strip().lower()
			if response != 'y':
				print("Cancelled")
				return

	# Insert links into database (unless --skip-db flag is set)
	if not skip_db and all_db_links:
		try:
			# Determine link type from config
			link_type = 'showlink' if config['entry_type'] == 'showlinks' else 'longread'

			# Create/open database
			db_conn = create_schema('ridehome.db')

			# Insert links
			inserted, duplicates = insert_links(db_conn, all_db_links, link_type)

			# Categorize newly inserted links with AI
			if inserted > 0 and os.environ.get('ANTHROPIC_API_KEY'):
				try:
					# Get titles that need categorization (newly inserted, no AI category yet)
					cursor = db_conn.cursor()
					titles_to_categorize = []
					for link in all_db_links:
						cursor.execute('SELECT ai_category FROM links WHERE title = ? LIMIT 1', (link['title'],))
						result = cursor.fetchone()
						if result and result[0] is None:
							titles_to_categorize.append(link['title'])

					if not titles_to_categorize:
						print("  (All links already categorized)")
					else:
						# Categorize with Claude API
						print(f"🤖 Categorizing {len(titles_to_categorize)} new links with AI...")
						categorizations = categorize_with_retry(titles_to_categorize, model='claude-haiku-4-5-20251001')

						# Update database with AI categories
						cursor = db_conn.cursor()
						categorized_count = 0
						for title, category in categorizations.items():
							cursor.execute('''
								UPDATE links
								SET ai_category = ?,
									ai_categorized_at = CURRENT_TIMESTAMP,
									ai_model = 'claude-haiku-4-5-20251001'
								WHERE title = ? AND ai_category IS NULL
							''', (category, title))
							if cursor.rowcount > 0:
								categorized_count += 1

						db_conn.commit()
						print(f"✓ Categorized {categorized_count} links")
				except Exception as e:
					print(f"⚠ Warning: AI categorization failed: {e}")
					print("  Links were saved but not categorized")

			db_conn.close()

			if inserted > 0:
				print(f"✓ Added {inserted} links to database (ridehome.db)")
			if duplicates > 0:
				print(f"  ({duplicates} duplicates skipped in database)")

			# Regenerate markdown files from database
			if inserted > 0:
				print("\n=== Regenerating markdown files ===")
				try:
					result = subprocess.run(['python3', 'rebuild_all.py'],
						capture_output=True, text=True, check=True)
					print(result.stdout)
				except subprocess.CalledProcessError as e:
					print(f"⚠ Warning: Failed to regenerate markdown: {e}")
					print(e.stdout)
					print(e.stderr)
		except Exception as e:
			print(f"⚠ Warning: Failed to update database: {e}")
			print("  No changes were made")


def process_type(feed_entries, extract_type, print_only=False, skip_db=False, yes=False):
	"""Process a single extraction type"""
	if extract_type not in CONFIGS:
		print(f"Error: Unknown type '{extract_type}'")
		return False

	config = CONFIGS[extract_type]

	if print_only:
		print_mode(feed_entries, config)
	else:
		update_mode(feed_entries, config, skip_db=skip_db, yes=yes)

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
	parser.add_argument(
		'--skip-db',
		action='store_true',
		help='Skip database updates (only update markdown files)'
	)
	parser.add_argument(
		'--yes', '-y',
		action='store_true',
		help='Skip confirmation prompts (for CI/automation)'
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
		process_type(rhfeed.entries, 'showlinks', print_only=False, skip_db=args.skip_db, yes=args.yes)
		print("\n=== Processing longreads ===")
		process_type(rhfeed.entries, 'longreads', print_only=False, skip_db=args.skip_db, yes=args.yes)

		# Update homepage status section after successful update
		if not args.skip_db:
			print("\n=== Updating homepage status ===")
			try:
				status_data = get_status_data()
				status_section = format_status_section(status_data)
				update_homepage(status_section)
				print("✓ Homepage status updated")
			except Exception as e:
				print(f"⚠ Warning: Failed to update homepage status: {e}")
	else:
		process_type(rhfeed.entries, args.type, print_only=args.print, skip_db=args.skip_db, yes=args.yes)

		# Update homepage status section after successful update (unless in print mode or skip-db)
		if not args.print and not args.skip_db:
			print("\n=== Updating homepage status ===")
			try:
				status_data = get_status_data()
				status_section = format_status_section(status_data)
				update_homepage(status_section)
				print("✓ Homepage status updated")
			except Exception as e:
				print(f"⚠ Warning: Failed to update homepage status: {e}")
