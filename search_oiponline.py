#!/usr/bin/env python3

import bs4
import urllib3
import json
import jieba
import string
import zhon.hanzi
import os
import pickle

http = urllib3.PoolManager()

BLOG_URL = 'http://www.oiponline.org/r/v1/sites/11209330/blog?expand=blogPosts&limit=1000&page=1&exclude_content=true'

def cache_http(filename, url):
	filepath = 'data/' + filename
	try:
		os.stat(filepath)
		data = open(filepath, 'r').read()
		if not data: # empty file is same as no file at all
			raise FileNotFoundError
	except FileNotFoundError:
		print('fetching ' + url)
		r = http.request('GET', url)
		if r.status != 200:
			raise 'error fetching ' + url
		data = r.data.decode('utf-8')
		open(filepath, 'w+').write(data)
	return data

def cache_http_json(filename, url):
	json_text = cache_http(filename, url)
	return json.loads(json_text)

def get_posts():
	posts = cache_http_json('blog.json', BLOG_URL)
	urls = [ {'id': post['id'], 'publicUrl': post['publicUrl'], 'title': post['title'], 'iconUrl': post['iconUrl'] } for post in posts['data']['blog']['blogPosts']]
	return urls

def get_stopwords():
	stopwords_cn = cache_http_json('zh.json', 'https://raw.githubusercontent.com/6/stopwords-json/master/dist/zh.json')
	stopwords_en = cache_http_json('en.json', 'https://raw.githubusercontent.com/6/stopwords-json/master/dist/en.json')
	stopwords = stopwords_cn + stopwords_en + list(string.punctuation) + list(zhon.hanzi.punctuation)
	return stopwords

def extract_keywords(content, stopwords):
	seg_list = jieba.cut(content, cut_all=False)
	words = set([s.strip().upper() for s in seg_list if len(s.strip())>1 and s not in stopwords])
	return words

stopwords = get_stopwords()
posts = get_posts()
for post in posts:
	post_id = str(post['id'])
	html_doc = cache_http(post_id + '.html', post['publicUrl'])
	soup = bs4.BeautifulSoup(html_doc, 'html.parser')
	contents = soup.select('.s-component-content > p')
	if contents:
		contents_str = [s.string for s in contents if s.string is not None]
		content = ' '.join(contents_str)
		post['keywords'] = extract_keywords(content, stopwords)
		pickle.dump(post, open('data/' + post_id + '.pkl', 'wb+'))

pickle.dump(posts, open('data/posts.pkl', 'wb+'))
