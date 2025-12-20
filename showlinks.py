# -*- coding: utf-8 -*-

import feedparser
import html2text
import re
import time
from bs4 import BeautifulSoup

FEED_URL = 'https://rss.art19.com/techmeme-ridehome'
# FEED_URL = 'https://rss.art19.com/coronavirus-daily-briefing'

def parse_feed(url):
    return feedparser.parse(url)

def format_post_time(post):
    return time.strftime("%A, %B %d %Y", post.published_parsed)

def get_podcast_title(post):
    title_parts = post.title.split(' - ')
    return title_parts[1] if len(title_parts) > 1 else title_parts[0]

def extract_links(soup):
    links_block = soup.find_all("p", string=re.compile("Links(:*)$|Stories:$"))
    if links_block and links_block[0].next_sibling.find_all('li'):
        return html2text.html2text(str(links_block[0].next_sibling))
    uls = soup.find_all("ul")
    if len(uls) == 1:
        return html2text.html2text(str(uls[0]))
    return "No show links for this episode ¯\_(ツ)_/¯\n"

def extract_sponsors(soup):
    sponsors_block = soup.find_all("p", string=re.compile("^Sponsors(:*)(\ *)$"))
    if sponsors_block and sponsors_block[0].next_sibling.find_all('li'):
        return html2text.html2text(str(sponsors_block[0].next_sibling))
    return None

def process_feed(feed):
    for post in feed.entries:
        post_pub_time = format_post_time(post)
        pod_title = get_podcast_title(post)
        print(f"\n**{post_pub_time} - {pod_title}**\n")
        
        clean_post = post.summary.replace('\n', '')
        soup = BeautifulSoup(clean_post, 'html5lib')
        
        links = extract_links(soup)
        print(links)
        
        sponsors = extract_sponsors(soup)
        if sponsors:
            print(sponsors)

if __name__ == "__main__":
    feed = parse_feed(FEED_URL)
    process_feed(feed)

