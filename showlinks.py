#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import feedparser
import html2text
import time
from html_parser import find_links_section

feedUrl = 'https://feeds.megaphone.fm/ridehome'
#feedUrl = 'https://rss.art19.com/coronavirus-daily-briefing'
rhfeed = feedparser.parse(feedUrl)

for post in rhfeed.entries:
	postPubTime = time.strftime("%A, %B %d %Y" ,post.published_parsed)
	podTitle = ""
	podTitleArray = post.title.split(' - ')
	if len(podTitleArray) > 1:
		podTitle = podTitleArray[1]
	else:
		podTitle = podTitleArray[0]

	print ("\n**" + postPubTime + " - " + podTitle + "**\n")
	
	# Try to get HTML content from content:encoded first, fall back to summary
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
		print("No content found for this episode\n")
		continue
	
	cleanPost = htmlContent.replace('\n', '')

	# Use shared HTML parser to find links section
	links_ul = find_links_section(cleanPost)

	if links_ul:
		html = html2text.html2text(str(links_ul))
		print(html)
	else:
		print("No show links for this episode ¯\\_(ツ)_/¯\n")

