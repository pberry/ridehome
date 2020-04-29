# -*- coding: utf-8 -*-

import feedparser
import html2text
import re
import time
from bs4 import BeautifulSoup
from bs4.diagnose import diagnose

feedUrl = 'https://techmeme.com/techmeme-ride-home-feed'
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
	cleanPost = post.summary.replace('\n', '')
	soup = BeautifulSoup(cleanPost, 'html5lib')
	linksBlock = soup.find_all("p", string=re.compile("Links(:*)$|Stories:$"))
	
	# check to see if we found anything
	# specifically at least one paragraph stating Links were coming and that the following ul contains a tags
	# this is a horrible way to do things but it's working so far
	if len(linksBlock) > 0 and len(linksBlock[0].next_sibling.find_all('li')) > 0:
		ul = str(linksBlock[0].next_sibling)
		html = html2text.html2text(ul)
		print (html)
	else:
		uls = soup.find_all("ul")
		if len(uls) == 1:
			print(html2text.html2text(str(uls[0])))
		else:
			print("No show links for this episode ¯\_(ツ)_/¯\n")
	linksBlock = soup.find_all("p", string=re.compile("^Sponsors(:*)(\ *)$"))
	if len(linksBlock) > 0 and len(linksBlock[0].next_sibling.find_all('li')) > 0:
		ul = str(linksBlock[0].next_sibling)
		html = html2text.html2text(ul)
		#print ("**Sponsors:**\n")
		#print (html)
	#print("[Subscribe to the ad-free Premium Feed inside your podcast app here!](https://kimberlite.fm/ridehome/)\n")
	#print("[All show links](https://pberry.github.io/ridehome/all-links.html)")

