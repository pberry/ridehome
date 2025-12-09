#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import feedparser
import html2text
import time
from html_parser import find_section

rhfeed = feedparser.parse('https://feeds.megaphone.fm/ridehome')

for post in rhfeed.entries:
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
		continue

	cleanPost = htmlContent.replace('\n', '')
	postPubTime = time.strftime("%A, %B %d", post.published_parsed)

	# Try to find Longreads or Suggestions sections
	# Use specific pattern to avoid matching timestamps like "15:35 Longreads"
	longreads_ul = find_section(cleanPost, pattern="Weekend Longreads|Longreads Suggestions")

	if longreads_ul:
		print("**" + postPubTime + "**")
		print(html2text.html2text(str(longreads_ul)))
	