import requests
from lxml import html
import json
import time
import signal
from razorback.models import Link
from django.core.management.base import BaseCommand
from django.forms.models import model_to_dict
from csv import writer
from itertools import islice
import psycopg2

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

def request_page(link_obj):
	signal.signal(signal.SIGALRM, alarm_handler)
	signal.alarm(10)
	try:
		print("Now entering " + link_obj.point_b)
		return requests.get(link_obj.point_b)
		signal.alarm(0)
	except TimeOutException as ex:
		print(ex)
		Link.objects.filter(point_b=link_obj.point_b).update(visited=True)
		return
	except Exception as e:
		signal.alarm(0)
		print(str(e))
		return

# from https://www.geeksforgeeks.org/python-ways-to-find-nth-occurrence-of-substring-in-a-string/
def loc_third_slash(link):
	occurrence = 3
	inilist = [i for i in range(0, len(link)) 
			if link[i:].startswith('/')] 
	if len(inilist)>= 3:
		return inilist[occurrence-1]
	else: 
		return False

def parse_response(link_obj, response):
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
			if not link_obj.point_b is None:
				new_links.append([href, False, link_obj.id])
			else:
				new_links.append([href, False, None])
		elif (href):
			if(loc_third_slash(href)):
				new_url =  link_obj.point_b[0:loc_third_slash(href)]
				appended_link = new_url + href
			else:
				appended_link = link_obj.point_b + href
			if not link_obj.point_b is None:
				new_links.append([appended_link, False, link_obj.id])
			else:
				new_links.append([appended_link, False, None])
		else:
			print(href)
	print('Done parsing.')
	return new_links, response.content

def save_data(link_obj, new_links, content):
	print('Saving data...')
	insert_link_list(new_links)
	Link.objects.filter(point_b=link_obj.point_b).update(visited=True, content=content)
	print('Done saving data.')

class Command(BaseCommand):
	measurements = [['label', 'context', 'data']]
	requests_attempted = 0
	requests_succeeded = 0

	def handle(self, *args, **options):
		if (Link.objects.first() == None):
			x = int(input("how many urls do you want to seed? "))
			y = x + 1
			z = 1
			while z < y:
				url = ""
				while not (url[0:7] == 'http://' or url[0:8] == 'https://'):
					url = input("provide seed link #" + str(z) + ":")
					if not (url[0:7] == 'http://' or url[0:8] == 'https://'):
						print("NOTE: provide in http:// or https:// form")
				Link.objects.create(point_b=url)
				z = z + 1
		else:
			print("resuming crawl.")

		break_check = len(Link.objects.filter(visited=False))
		analytics_static_time = time.time()
		analytics_dynamic_time = time.time()
		while break_check > 0:
			loop_start = time.time()
			start = time.time()
			link = Link.objects.filter(visited=False).first()
			self.measurements.append(['model filter', {'code': 'Link.objects.filter(visited=False).first()'}, time.time() - start])
			if link:
				try:
					url = link.point_b
					if not link.visited:
						start = time.time()
						self.requests_attempted = self.requests_attempted + 1
						response = request_page(link)
						self.requests_succeeded = self.requests_succeeded + 1
						self.measurements.append(['request_page', {'link_object': link}, time.time() - start])
						start = time.time()
						new_links, content = parse_response(link, response)
						self.measurements.append(['parse_response', {'link_object': link, 'new_links': len(new_links), 'content_length': len(content)}, time.time() - start])
						start = time.time()
						save_data(link, new_links, content)
						self.measurements.append(['save_data', {'link_object': link, 'new_links': len(new_links), 'content_length': len(content)}, time.time() - start])
					else:
						print("link " + str(link.id) + " was already visited. Skipping...")
				except Exception as e:
					break_check = len(Link.objects.filter(visited=False))
			else:
				break_check = len(Links.objects.filter(visited=False))
			self.measurements.append(['loop', {'link_object': link}, time.time() - loop_start])
			if (time.time() - analytics_dynamic_time) > 10:
				for measurement in self.measurements:
					append_list_as_row('flashgordon_analytics.csv', measurement)
					self.measurements = []
				requests_per_second = self.requests_attempted / (time.time() - analytics_static_time)
				append_list_as_row('flashgordon_analytics.csv', ['requests_per_second', {'requests_attempted': self.requests_attempted, 'requests_succeeded': self.requests_succeeded}, requests_per_second])
				append_list_as_row('flashgordon_analytics.csv', ['request sucess ratio', {'requests_attempted': self.requests_attempted, 'requests_succeeded': self.requests_succeeded}, self.requests_succeeded / self.requests_attempted])
				
				analytics_dynamic_time = time.time()
