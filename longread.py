# -*- coding: utf-8 -*-
import feedparser
import re
import time
from bs4 import BeautifulSoup

longReads = 0
longReadWeeks = 0
rhfeed = feedparser.parse('https://techmeme.com/techmeme-ride-home-feed')
for post in rhfeed.entries:
	soup = BeautifulSoup(post.summary, 'html.parser')
	if "Longread" in post.summary :
		longReadWeeks += 1
		postPubTime = time.strftime("%A, %B %d" ,post.published_parsed)

		for paragraph in soup.find_all('p'):
			if "Longreads:" in paragraph.text:
				print ("\n**" + postPubTime + "**")
				for listItem in (paragraph.next_sibling.find_all('li')):
					longReads += 1
					print ("* [" + listItem.a.string + "](" + listItem.a['href'] + ")" + listItem.contents[1].string)
print ("Longreads: ",longReads)
print ("Longread Weeks: ",longReadWeeks)