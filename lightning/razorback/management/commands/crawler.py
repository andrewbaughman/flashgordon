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

def insert_link_list(link_list):
	"""
	Insert many Links into the the Link table
	"""
	sql = "INSERT INTO razorback_link(id, point_b, visited, point_a_id) VALUES(%s)"
	conn = None
	try:
		conn = psycopg2.connect(dbname="razorback_link", user="flash", password="password")
		cur = conn.cursor()
		cur.executemany(sql, link_list)
		conn.commit()
		cur.close()
	except (Exception, psycopg2.DatabaseError) as error:
		print(error)
	finally:
		if conn is not None:
			conn.close()


class Command(BaseCommand):
	measurements = [['point_a', 'point_b', 'process', 'duration']]
	requests_attempted = 0
	requests_succeeded = 0

	def handle(self, *args, **options):
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

		def get_page_of_links(link_obj):
			signal.signal(signal.SIGALRM, alarm_handler)
			signal.alarm(10)
			print("Now entering " + link_obj.point_b)
			try:
				start = time.time()
				self.requests_attempted = self.requests_attempted + 1
				page = requests.get(link_obj.point_b)
				self.measurements.append([link_obj.point_a, link_obj.point_b, 'request', time.time() - start])
				self.requests_succeeded = self.requests_succeeded + 1
				signal.alarm(0)
				start = time.time()
				tree = html.fromstring(page.content)
				self.measurements.append([link_obj.point_a, link_obj.point_b, 'parse_content', time.time() - start])
				start = time.time()
				links_a = tree.xpath('//a/@href')
			except TimeOutException as ex:
				print(ex)
				Link.objects.filter(point_b=link_obj.point_b).update(visited=True)
				return
			except Exception as e:
				signal.alarm(0)
				print(str(e))
				return
			start = time.time()
			Link.objects.filter(point_b=link_obj.point_b).update(visited=True)
			self.measurements.append([link_obj.point_a, link_obj.point_b, 'update_unvisited', time.time() - start])
			print("Visited " + url)
			start = time.time()
			new_links = []
			start = time.time()
			self.measurements.append([link_obj.point_a, link_obj.point_b, 'find_links', time.time() - start])
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
					if(loc_third_slash(url)):
						new_url =  url[0:loc_third_slash(url)]
						appended_link = new_url + href
					else:
						appended_link = url + href
					if not link_obj.point_b is None:
						new_links.append([appended_link, False, link_obj.id])
					else:
						new_links.append([appended_link, False, None])
				else:
					print(href)
					return
			
			self.measurements.append([link_obj.point_a, link_obj.point_b, 'process_links', time.time() - start])
			start = time.time()
			# for link in new_links:
			# 	Link.objects.create(link)
			insert_link_list(new_links)
			# Link.objects.bulk_create(new_links)
			self.measurements.append([link_obj.point_a, link_obj.point_b, 'save_data', time.time() - start])
			
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
			start = time.time()
			link = Link.objects.filter(visited=False).first()
			self.measurements.append([link.point_a, link.point_b, 'first_unvisited', time.time() - start])
			if link:
				try:
					url = link.point_b
					if not link.visited:
						start_n = time.time()
						get_page_of_links(link)
						self.measurements.append([link.point_a, link.point_b, 'get_page_of_links', time.time() - start_n])
					else:
						print("link " + str(link.id) + " was already visited. Skipping...")
				except Exception as e:
					break_check = len(Link.objects.filter(visited=False))
			else:
				break_check = len(Links.objects.filter(visited=False))
			self.measurements.append([link.point_a, link.point_b, 'main_loop', time.time() - start])
			if (time.time() - analytics_dynamic_time) > 10:
				for measurement in self.measurements:
					append_list_as_row('flashgordon_analytics.csv', measurement)
					self.measurements = []
				requests_per_second = self.requests_attempted / (time.time() - analytics_static_time)
				append_list_as_row('flashgordon_analytics.csv', [None,self.requests_attempted,"Requests per second", requests_per_second])
				append_list_as_row('flashgordon_analytics.csv', [self.requests_succeeded,self.requests_attempted,"Requests success ratio", self.requests_succeeded / self.requests_attempted])
				analytics_dynamic_time = time.time()
