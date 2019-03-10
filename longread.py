# -*- coding: utf-8 -*-
import configparser
import feedparser
import html2text
import re
import time
from bs4 import BeautifulSoup

config = configparser.ConfigParser()
config.read('config.cfg')
pbkey = config["Main"]["pinboardkey"]

rhfeed = feedparser.parse('https://techmeme.com/techmeme-ride-home-feed')

for post in rhfeed.entries:
	cleanPost = post.content[0]['value'].replace('\n','')
	soup = BeautifulSoup(cleanPost, 'html.parser')
	postPubTime = time.strftime("%A, %B %d" ,post.published_parsed)

	for paragraph in soup.find_all('p'):
		if "Longreads" in paragraph.text or "Suggestions:" in paragraph.text:
			# print (paragraph)
			print ("**" + postPubTime + "**")
			print (html2text.html2text(str(paragraph.next_sibling)))
		else:
			print ("Nope: " + str(paragraph))
	print("[All long reads](https://pberry.github.io/ridehome/longreads.html)")