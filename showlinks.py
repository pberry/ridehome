# -*- coding: utf-8 -*-
import feedparser
import html2text
import re
import time
from bs4 import BeautifulSoup

rhfeed = feedparser.parse('https://techmeme.com/techmeme-ride-home-feed')

for post in rhfeed.entries:
	postPubTime = time.strftime("%A, %B %d %Y" ,post.published_parsed)
	podTitle = ""
	podTitleArray = post.itunes_title.split(' - ')
	if len(podTitleArray) > 1:
		podTitle = podTitleArray[1]
	else:
		podTitle = podTitleArray[0]

	print ("\n**" + postPubTime + " - " + podTitle + "**\n")

	soup = BeautifulSoup(post.summary, 'html.parser')
	linksBlock = soup.find_all("p", string=re.compile("^Links(:*)(\ *)$|Stories:$"))

	# check to see if we found anything
	# specifically at least one paragraph stating Links were coming and that the following ul contains a tags
	# this is a horrible way to do things but it's working so far
	if len(linksBlock) > 0 and len(linksBlock[0].next_sibling.find_all('li')) > 0:
		ul = str(linksBlock[0].next_sibling)
		html = html2text.html2text(ul)
		print (html)
	else:
		print("No show links for this episode ¯\_(ツ)_/¯\n")

