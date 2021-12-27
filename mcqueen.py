import requests
from lxml import html
import signal
import psycopg2
import multiprocessing
from multiprocessing import Process, Pool
import concurrent.futures
import time

# import requests_cache DNS Caching decreased performance slightly, but might be helpful in the future. 

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
	# print('Parsing response...')
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
	# print('Done parsing.')
	return new_links, response.content

def save_data(link, new_links, content):
	# print('Saving data...')
	insert_link_list(new_links)
	if link['point_a_id'] == None:
		id = run_sql("""UPDATE razorback_link SET visited=TRUE, content=%s WHERE point_b=%s RETURNING id;""", [content, link['point_b']])
	else:
		id = run_sql("""UPDATE razorback_link SET visited=TRUE, content=%s WHERE point_b=%s AND point_a_id=%s RETURNING id;""", [content, link['point_b'], link['point_a_id']])
	run_sql("""UPDATE razorback_link SET taken=FALSE WHERE id=%s RETURNING id;""", [id])
	# print('Done saving data.')

def request_page(link):
	signal.signal(signal.SIGALRM, alarm_handler)
	signal.alarm(10)
	try:
		# print("Now entering " + link['point_b'])
		# response = self.session.get(link['point_b'])
		response = requests.get(link['point_b'])
		return response
		signal.alarm(0)
	except TimeOutException as ex:
		print(ex)
		run_sql("""UPDATE razorback_link SET visited=True WHERE point_b=%s AND point_a_id=%s RETURNING id;""", [link['point_b'], link['point_a_id']])
	except Exception as e:
		signal.alarm(0)
		print(str(e))
		return

def main_loop(break_check):
	link = run_sql("""SELECT * FROM razorback_link WHERE visited=FALSE AND taken=FALSE FETCH FIRST ROW ONLY;""")
	link = {
		'id': link[0],
		'point_b': link[1],
		'visited': link[2],
		'point_a_id': link[3],
		'content': link[4]
	}
	run_sql("""UPDATE razorback_link SET taken=TRUE WHERE id=%s RETURNING id;""", [link['id']])
	if link:
		try:
			url = link['point_b']
			if not link['visited']:
				start = time.time()
				response = request_page(link)
				# print(f"{time.time() - start} seconds for requesting {link['point_b']}")
				new_links, content = parse_response(link, response)
				save_data(link, new_links, content)
			else:
				# print("link " + str(link['id']) + " was already visited. Skipping...")
				pass
		except Exception as e:
			break_check = run_sql("""SELECT COUNT(*) FROM razorback_link WHERE visited=False;""")[0]
	else:
		break_check = run_sql("""SELECT COUNT(*) FROM razorback_link WHERE visited=False;""")[0]
	return break_check
	

if __name__ == '__main__':
	processes = []

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
	# while break_check > 0:
		# break_check= main_loop(break_check)

	with concurrent.futures.ProcessPoolExecutor() as executor:
		results = []

		while break_check > 0:
			time.sleep(0.2)
			results.append(executor.submit(main_loop, [break_check]))
			
		for f in concurrent.futures.as_completed(results):
			break_check = f.result()[0]
