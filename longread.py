# -*- coding: utf-8 -*-
import feedparser
import html2text
import re
import time
from bs4 import BeautifulSoup

rhfeed = feedparser.parse('https://techmeme.com/techmeme-ride-home-feed')
for post in rhfeed.entries:
	soup = BeautifulSoup(post.summary, 'html.parser')
	if "Longread" in post.summary :

		postPubTime = time.strftime("%A, %B %d" ,post.published_parsed)

		for paragraph in soup.find_all('p'):
			if "Longreads:" in paragraph.text or "Suggestions:" in paragraph.text:
				print ("**" + postPubTime + "**")
				print (html2text.html2text(str(paragraph.next_sibling)))