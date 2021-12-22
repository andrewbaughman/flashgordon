import requests
from lxml import html
import json
import time
import signal
from csv import writer
from itertools import islice
import psycopg2
import tldextract
# import requests_cache DNS Caching decreased performance slightly, but might be helpful in the future. 


# https://thispointer.com/python-how-to-append-a-new-row-to-an-existing-csv-file/
def append_list_as_row(file_name, list_of_elem):
	with open(file_name, 'a+', newline='') as write_obj:
		csv_writer = writer(write_obj)
		csv_writer.writerow(list_of_elem)

def insert_link(link):
	""" insert a new link into the Link table """
	sql = """INSERT INTO razorback_link(point_b, visited, point_a_id) VALUES(%s,%s,%s) RETURNING id;"""
	conn = None
	id = None
	try:
		conn = psycopg2.connect(dbname="lightning_db", user="flash", password="password")
		cur = conn.cursor()
		cur.execute(sql, link)
		id = cur.fetchone()[0]
		conn.commit()
		cur.close()
	except (Exception, psycopg2.DatabaseError) as error:
		print(error)
	finally:
		if conn is not None:
			conn.close()

def insert_link_list(link_list):
	"""
	Insert many Links into the the Link table
	"""
	sql = """INSERT INTO razorback_link(point_b, visited, point_a_id) VALUES(%s,%s,%s)"""
	conn = None
	try:
		conn = psycopg2.connect(dbname="lightning_db", user="flash", password="password")
		cur = conn.cursor()
		cur.executemany(sql, link_list)
		conn.commit()
		cur.close()
	except (Exception, psycopg2.DatabaseError) as error:
		print(error)
	finally:
		if conn is not None:
			conn.close()

#https://code-maven.com/python-timeout
class TimeOutException(Exception):
	pass

def alarm_handler(signum, frame):
	print("timeout has occured")
	raise TimeOutException()

# from https://www.geeksforgeeks.org/python-ways-to-find-nth-occurrence-of-substring-in-a-string/
def loc_third_slash(link):
	occurrence = 3
	inilist = [i for i in range(0, len(link)) 
			if link[i:].startswith('/')] 
	if len(inilist)>= 3:
		return inilist[occurrence-1]
	else: 
		return False

def parse_response(link, response):
	print('Parsing response...')
	tree = html.fromstring(response.content)
	links_a = tree.xpath('//a/@href')
	new_links = []
	links_a = list(dict.fromkeys(links_a))
	for href in links_a:
		if href == None:
			continue
		elif len(href) < 3:
			continue
		elif ('#' in href) or ('@' in href):
			continue
		elif (href[0:7] == 'http://' or href[0:8] == 'https://' or href[0:4] == 'www.'):
			if not link['point_b'] is None:
				new_links.append([href, False, link['id']])
			else:
				new_links.append([href, False, None])
		elif (href):
			if(loc_third_slash(href)):
				new_url =  link['point_b'][0:loc_third_slash(href)]
				appended_link = new_url + href
			else:
				appended_link = link['point_b'] + href
			if not link['point_b'] is None:
				new_links.append([appended_link, False, link['id']])
			else:
				new_links.append([appended_link, False, None])
		else:
			print(href)
	print('Done parsing.')
	return new_links, response.content

def save_data(link, new_links, content):
	print('Saving data...')
	insert_link_list(new_links)
	
	""" update a link in the Link table """
	sql = """UPDATE razorback_link SET visited=True, content=%s WHERE point_b=%s RETURNING id;"""
	conn = None
	id = None
	try:
		conn = psycopg2.connect(dbname="lightning_db", user="flash", password="password")
		cur = conn.cursor()
		cur.execute(sql, [content, link['point_b']])
		id = cur.fetchone()[0]
		conn.commit()
		cur.close()
	except (Exception, psycopg2.DatabaseError) as error:
		print(error)
	finally:
		if conn is not None:
			conn.close()
	print('Done saving data.')

def get_count():
	""" get count of links in the Link table """
	sql = """SELECT COUNT(*) FROM razorback_link;"""
	conn = None
	count = None
	try:
		conn = psycopg2.connect(dbname="lightning_db", user="flash", password="password")
		cur = conn.cursor()
		cur.execute(sql)
		count = cur.fetchone()[0]
		conn.commit()
		cur.close()
	except (Exception, psycopg2.DatabaseError) as error:
		print(error)
	finally:
		if conn is not None:
			conn.close()
	return count

def count_unvisited():
	""" get count of unvisited links in the Link table """
	sql = """SELECT COUNT(*) FROM razorback_link WHERE visited=False;"""
	conn = None
	count = None
	try:
		conn = psycopg2.connect(dbname="lightning_db", user="flash", password="password")
		cur = conn.cursor()
		cur.execute(sql)
		count = cur.fetchone()[0]
		conn.commit()
		cur.close()
	except (Exception, psycopg2.DatabaseError) as error:
		print(error)
	finally:
		if conn is not None:
			conn.close()
	return count

def first_unvisited():
	""" get first link in the Link table """
	sql = """SELECT * FROM razorback_link WHERE visited=False FETCH FIRST ROW ONLY;"""
	conn = None
	id = None
	link = None
	try:
		conn = psycopg2.connect(dbname="lightning_db", user="flash", password="password")
		cur = conn.cursor()
		cur.execute(sql)
		id = cur.fetchone()[0]
		conn.commit()
		cur.close()
	except (Exception, psycopg2.DatabaseError) as error:
		print(error)
	finally:
		if conn is not None:
			conn.close()

	try:
		sql = """SELECT * FROM razorback_link WHERE id=%s;"""
		conn = psycopg2.connect(dbname="lightning_db", user="flash", password="password")
		cur = conn.cursor()
		cur.execute(sql, [id])
		link = cur.fetchone()
		conn.commit()
		cur.close()
	except (Exception, psycopg2.DatabaseError) as error:
		print(error)
	finally:
		if conn is not None:
			conn.close()
	return link

def request_page(link):
	signal.signal(signal.SIGALRM, alarm_handler)
	signal.alarm(10)
	try:
		print("Now entering " + link['point_b'])
		# response = self.session.get(link['point_b'])
		response = requests.get(link['point_b'])
		return response
		signal.alarm(0)
	except TimeOutException as ex:
		print(ex)
		""" update a link in the Link table """
		sql = """UPDATE razorback_link SET visited=True WHERE point_b=%s RETURNING id;"""
		conn = None
		id = None
		try:
			conn = psycopg2.connect(dbname="lightning_db", user="flash", password="password")
			cur = conn.cursor()
			cur.execute(sql, [link['point_b']])
			id = cur.fetchone()[0]
			conn.commit()
			cur.close()
		except (Exception, psycopg2.DatabaseError) as error:
			print(error)
		finally:
			if conn is not None:
				conn.close()
		return
	except Exception as e:
		signal.alarm(0)
		print(str(e))
		return


def __main__():
	measurements = [['label', 'context', 'data']]
	requests_attempted = 0
	requests_succeeded = 0

	if (get_count() == 0):
		x = int(input("how many urls do you want to seed? "))
		y = x + 1
		z = 1
		while z < y:
			url = ""
			while not (url[0:7] == 'http://' or url[0:8] == 'https://'):
				url = input("provide seed link #" + str(z) + ":")
				if not (url[0:7] == 'http://' or url[0:8] == 'https://'):
					print("NOTE: provide in http:// or https:// form")
			insert_link([url, False, None])
			z = z + 1
	else:
		print("resuming crawl.")

	break_check = count_unvisited()
	analytics_static_time = time.time()
	analytics_dynamic_time = time.time()
	while break_check > 0:
		loop_start = time.time()
		start = time.time()
		link = first_unvisited()
		link = {
			'id': link[0],
			'point_b': link[1],
			'visited': link[2],
			'point_a_id': link[3],
			'content': link[4]
		}
		measurements.append(['model filter', {'code': 'Link.objects.filter(visited=False).first()'}, time.time() - start])
		if link:
			try:
				url = link['point_b']
				if not link['visited']:
					start = time.time()
					requests_attempted = requests_attempted + 1
					response = request_page(link)
					requests_succeeded = requests_succeeded + 1
					measurements.append(['request_page', {'destination': link['point_b'], 'source': link['point_a_id']}, time.time() - start])
					start = time.time()
					new_links, content = parse_response(link, response)
					measurements.append(['parse_response', {'link_object': link, 'new_links': len(new_links), 'content_length': len(content)}, time.time() - start])
					start = time.time()
					save_data(link, new_links, content)
					measurements.append(['save_data', {'link_object': link, 'new_links': len(new_links), 'content_length': len(content)}, time.time() - start])
				else:
					print("link " + str(link['id']) + " was already visited. Skipping...")
			except Exception as e:
				break_check = count_unvisited()
		else:
			break_check = count_unvisited()
		measurements.append(['loop', {'link_object': link}, time.time() - loop_start])
		if (time.time() - analytics_dynamic_time) > 10:
			for measurement in measurements:
				append_list_as_row('flashgordon_analytics.csv', measurement)
				measurements = []
			requests_per_second = requests_attempted / (time.time() - analytics_static_time)
			append_list_as_row('flashgordon_analytics.csv', ['requests_per_second', {'requests_attempted': requests_attempted, 'requests_succeeded': requests_succeeded}, requests_per_second])
			append_list_as_row('flashgordon_analytics.csv', ['request sucess ratio', {'requests_attempted': requests_attempted, 'requests_succeeded': requests_succeeded}, requests_succeeded / requests_attempted])
			
			analytics_dynamic_time = time.time()


# class Command(BaseCommand):
# 	measurements = [['label', 'context', 'data']]
# 	requests_attempted = 0
# 	requests_succeeded = 0
# 	session = requests.Session()
# 	# session = requests_cache.CachedSession() DNS Caching


__main__()