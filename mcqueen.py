import requests
from lxml import html
import json
import time
import signal
from csv import writer
from itertools import islice
import psycopg2
import tldextract
from multiprocessing import Process

# import requests_cache DNS Caching decreased performance slightly, but might be helpful in the future. 


# https://thispointer.com/python-how-to-append-a-new-row-to-an-existing-csv-file/
def append_list_as_row(file_name, list_of_elem):
	with open(file_name, 'a+', newline='') as write_obj:
		csv_writer = writer(write_obj)
		csv_writer.writerow(list_of_elem)

def run_sql(sql, params=None):
	""" Run any sql string on the lightning_db database"""
	conn = None
	ret = None
	try:
		conn = psycopg2.connect(dbname="lightning_db", user="flash", password="password")
		cur = conn.cursor()
		cur.execute(sql, params)
		ret = cur.fetchone()
		conn.commit()
		cur.close()
	except (Exception, psycopg2.DatabaseError) as error:
		print(error)
	finally:
		if conn is not None:
			conn.close()
	return ret

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
	run_sql("""UPDATE razorback_link SET visited=True, content=%s WHERE point_b=%s RETURNING id;""", [content, link['point_b']])
	print('Done saving data.')

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
		run_sql("""UPDATE razorback_link SET visited=True WHERE point_b=%s RETURNING id;""", [link['point_b']])
	except Exception as e:
		signal.alarm(0)
		print(str(e))
		return



def main_loop():
	request_succeeded = False
	measurements = []
	loop_start = time.time()
	start = time.time()
	link = run_sql("""SELECT * FROM razorback_link WHERE visited=False FETCH FIRST ROW ONLY;""")
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
				response = request_page(link)
				measurements.append(['request_page', {'destination': link['point_b'], 'source': link['point_a_id']}, time.time() - start])
				if response.ok:
					request_succeeded = True
				start = time.time()
				new_links, content = parse_response(link, response)
				measurements.append(['parse_response', {'link_object': link, 'new_links': len(new_links), 'content_length': len(content)}, time.time() - start])
				start = time.time()
				save_data(link, new_links, content)
				measurements.append(['save_data', {'link_object': link, 'new_links': len(new_links), 'content_length': len(content)}, time.time() - start])
			else:
				print("link " + str(link['id']) + " was already visited. Skipping...")
		except Exception as e:
			break_check = run_sql("""SELECT COUNT(*) FROM razorback_link WHERE visited=False;""")[0]
	else:
		break_check = run_sql("""SELECT COUNT(*) FROM razorback_link WHERE visited=False;""")[0]
	measurements.append(['loop', {'link_object': link}, time.time() - loop_start])
	return measurements, request_succeeded
	


def __main__():
	append_list_as_row('flashgordon_analytics.csv', ['label', 'context', 'data'])
	requests_attempted = 0
	requests_succeeded = 0
	
	if (run_sql("""SELECT COUNT(*) FROM razorback_link;""")[0] == 0):
		x = int(input("how many urls do you want to seed? "))
		y = x + 1
		z = 1
		while z < y:
			url = ""
			while not (url[0:7] == 'http://' or url[0:8] == 'https://'):
				url = input("provide seed link #" + str(z) + ":")
				if not (url[0:7] == 'http://' or url[0:8] == 'https://'):
					print("NOTE: provide in http:// or https:// form")
			run_sql("""INSERT INTO razorback_link(point_b, visited, point_a_id) VALUES(%s,FALSE,NULL) RETURNING id;""", [url])
			z = z + 1
	else:
		print("resuming crawl.")

	break_check = run_sql("""SELECT COUNT(*) FROM razorback_link WHERE visited=False;""")[0]
	analytics_static_time = time.time()
	analytics_dynamic_time = time.time()
	requests_succeeded = 0
	measurements = []
	while break_check > 0:
		ext_measurements, request_succeeded = main_loop()
		measurements.extend(ext_measurements)
		if request_succeeded:
			requests_succeeded = requests_succeeded + 1

		if (time.time() - analytics_dynamic_time) > 10:
			for measurement in measurements:
				append_list_as_row('flashgordon_analytics.csv', measurement)
				measurements = []

			requests_per_second = requests_succeeded / (time.time() - analytics_static_time)
			append_list_as_row('flashgordon_analytics.csv', ['requests_per_second', {'requests_attempted': requests_attempted, 'requests_succeeded': requests_succeeded}, requests_per_second])
			
			analytics_dynamic_time = time.time()


__main__()