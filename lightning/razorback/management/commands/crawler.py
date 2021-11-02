import requests
from bs4 import BeautifulSoup
import json
import time
import signal
from razorback.models import Link
from django.core.management.base import BaseCommand
from django.forms.models import model_to_dict
from csv import writer

# https://thispointer.com/python-how-to-append-a-new-row-to-an-existing-csv-file/
def append_list_as_row(file_name, list_of_elem):
    with open(file_name, 'a+', newline='') as write_obj:
        csv_writer = writer(write_obj)
        csv_writer.writerow(list_of_elem)


class Command(BaseCommand):
	measurements = [['point_a', 'point_b', 'process', 'duration']]

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
				page = requests.get(link_obj.point_b)
				self.measurements.append([link_obj.point_a, link_obj.point_b, 'request', time.time() - start])
				signal.alarm(0)
				start = time.time()
				soup = BeautifulSoup(page.content, 'html.parser')
				self.measurements.append([link_obj.point_a, link_obj.point_b, 'parse_content', time.time() - start])
				start = time.time()
				links_a = soup.findAll('a')
			except TimeOutException as ex:
				print(ex)
				Link.objects.filter(point_b=link_obj.point_b).update(visited=True)
				return
			except Exception as e:
				signal.alarm(0)
				print(str(e))
				return
			Link.objects.filter(point_b=link_obj.point_b).update(visited=True)
			# print("Visited " + url)
			start = time.time()
			new_links = []
			start = time.time()
			self.measurements.append([link_obj.point_a, link_obj.point_b, 'find_links', time.time() - start])
			for link in links_a:
				href = link.get('href')
				if href == None:
					continue
				elif len(href) < 3:
					continue
				elif ('#' in href) or ('@' in href):
					continue
				elif (href[0:7] == 'http://' or href[0:8] == 'https://' or href[0:4] == 'www.'):
					if not link_obj.point_b is None:
						new_links.append(Link(point_b=href, point_a=link_obj))
					else:
						new_links.append(Link(point_b=href))
				elif (href):
					if(loc_third_slash(url)):
						new_url =  url[0:loc_third_slash(url)]
						appended_link = new_url + href
					else:
						appended_link = url + href
					if not link_obj.point_b is None:
						new_links.append(Link(point_b=appended_link, point_a=link_obj))
					else:
						new_links.append(Link(point_b=appended_link))
				else:
					return
			self.measurements.append([link_obj.point_a, link_obj.point_b, 'process_links', time.time() - start])
			start = time.time()
			Link.objects.bulk_create(new_links)
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
		analytics_save_time = time.time()
		while break_check > 0:
			start = time.time()
			link = Link.objects.filter(visited=False).first()
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
			if time.time() - analytics_save_time > 10:
				for measurement in self.measurements:
					append_list_as_row('flashgordon_analytics.csv', measurement)
					self.measurements = []
