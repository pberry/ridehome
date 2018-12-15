# -*- coding: utf-8 -*-
import feedparser
import re
import time
from bs4 import BeautifulSoup

def get_sec(time_str):
	h, m, s = time_str.split(':')
	return int(h) * 3600 + int(m) * 60 + int(s)

rhfeed = feedparser.parse('https://techmeme.com/techmeme-ride-home-feed')
linkCount = 0
podCount = 0
totalTime = 0
for post in rhfeed.entries:
	postPubTime = time.strftime("%A, %B %d" ,post.published_parsed)
	print ("\n**" + postPubTime + "**")
	totalTime += get_sec(post.itunes_duration)
	podCount += 1
	soup = BeautifulSoup(post.summary, 'html.parser')
	linksBlock = soup.find_all("p", string="Links:")
	# check to see if we found anything
	# specifically at least one paragraph stating Links were coming and that the following ul contains a tags
	if len(linksBlock) > 0 and len(linksBlock[0].next_sibling.find_all('a')) > 0:
		for listItem in (linksBlock[0].next_sibling.find_all('li')):
			linkCount += 1
			if listItem.a:
				if len(listItem.contents) == 2:
					print ("* [" + listItem.a.string + "](" + listItem.a['href'] + ") " + listItem.contents[1].string.strip())
				else:
					print ("* [" + listItem.a.string + "](" + listItem.a['href'] + ")")
print ("Link count: ",linkCount)
print ("Pod count: ",podCount)
print ("Total pod time in seconds:",totalTime)

