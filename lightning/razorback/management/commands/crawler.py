import requests
from bs4 import BeautifulSoup
import json
import time
import signal
from razorback.models import Link
from django.core.management.base import BaseCommand
from django.forms.models import model_to_dict


class Command(BaseCommand):

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
			print("Now entering " + link_obj['point_b'])
			try:
				page = requests.get(link_obj['point_b'])
				signal.alarm(0)
				soup = BeautifulSoup(page.content, 'html.parser')
				links_a = soup.findAll('a')
			except TimeOutException as ex:
				print(ex)
				Link.objects.filter(point_b=link_obj['point_b']).update(visited=True)
				return
			except Exception as e:
				signal.alarm(0)
				print(str(e))
				return
			Link.objects.filter(point_b=link_obj['point_b']).update(visited=True)
			print("Visited " + url)
			for link in links_a:
				href = link.get('href')
				if href == None:
					continue
				elif len(href) < 3:
					continue
				elif ('#' in href) or ('@' in href):
					continue
				elif (href[0:7] == 'http://' or href[0:8] == 'https://' or href[0:4] == 'www.'):
					if not link_obj['point_b'] is None:
						Link.objects.create(point_b=href, point_a=Link.objects.get(id=link_obj['id']))
					else:
						Link.objects.create(point_b=href)
				elif (href):
					if(loc_third_slash(url)):
						new_url =  url[0:loc_third_slash(url)]
						appended_link = new_url + href
					else:
						appended_link = url + href
					if not link_obj['point_b'] is None:
						Link.objects.create(point_b=href, point_a=Link.objects.get(id=link_obj['id']))
					else:
						Link.objects.create(point_b=href)

				else:
					return
			
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
		while break_check > 0:
			link = Link.objects.filter(visited=False).first()
			if link:
				try:
					url = link.point_b
					if not link.visited:
						get_page_of_links(model_to_dict(link))
					else:
						print("link #" + str(i) + " was already visited. Skipping...")
				except Exception as e:
					break_check = len(Link.objects.filter(visited=False))
			else:
				break_check = len(Links.objects.filter(visited=False))
