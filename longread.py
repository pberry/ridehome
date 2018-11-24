# -*- coding: utf-8 -*-
import feedparser
import re
import time
from bs4 import BeautifulSoup

rhfeed = feedparser.parse('https://techmeme.com/techmeme-ride-home-feed')
for post in rhfeed.entries:
   	if "Longread" in post.summary :
   		soup = BeautifulSoup(post.summary, 'html.parser')
   		postPubTime = time.strftime("%A, %B %d" ,post.published_parsed)

   		for paragraph in soup.find_all('p'):
   			if "Longreads:" in paragraph.text:
   				print ("\n**" + postPubTime + "**")
   				for listItem in (paragraph.next_sibling.find_all('li')):
   					print ("* [" + listItem.a.string + "](" + listItem.a['href'] + ")" + listItem.contents[1].string)
