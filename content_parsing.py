from lxml import html

# from https://www.geeksforgeeks.org/python-ways-to-find-nth-occurrence-of-substring-in-a-string/
def loc_third_slash(url):
	slash_locations = [i for i in range(0, len(url)) if url[i:].startswith('/')]
	return slash_locations[2]

def has_third_slash(url):
	slash_locations = [i for i in range(0, len(url)) if url[i:].startswith('/')]
	return len(slash_locations) >= 3

def links_from_urls(link, urls):
	links = []
	for url in urls:
		if link['point_b']:
			links.append([url, False, link['id'], False])
		else:
			links.append([url, False, None, False])

	return links

def attempt_to_fix_href(point_b, href):
	if len(href) < 3:
		raise Exception(f"href cannot be fixed yet, is less than 3 characters long: {href}")
	elif href.startswith('#'):
		raise Exception(f"href cannot be fixed yet, starts with #: {href}")
	elif '@' in href:
		raise Exception(f"href cannot be fixed yet, has @: {href}")
	elif href.startswith('/'):
		raise Exception(f"href cannot be fixed yet, starts with /: {href}")
	else:
		raise Exception(f"href cannot be fixed yet, is unusual: {href}")

def parse_href(point_b, href):
	if href == None:
		raise Exception("href is None")
	elif href_needs_no_doctor(href):
		return href
	else:
		return attempt_to_fix_href(point_b, href)

def href_needs_no_doctor(href):
	if href[0:7] == 'http://':
		return True
	elif href[0:8] == 'https://':
		return True
	elif href[0:4] == 'www.':
		return True
	else:
		return False

def get_urls_from_page(point_b, content):
	tree = html.fromstring(content)
	hrefs = list(dict.fromkeys(tree.xpath('//a/@href')))
	urls = []
	for href in hrefs:
		try:
			urls.append(parse_href(point_b, href))
		except Exception as e:
			# print(str(e))
			pass

	return urls