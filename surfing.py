from content_parsing import *
from db_utils import *
import requests
import signal
import time

#https://code-maven.com/python-timeout
class TimeOutException(Exception):
	pass

def alarm_handler(signum, frame):
	raise TimeOutException()

def update_visited_link(link, content):
	run_sql("""UPDATE razorback_link SET visited=TRUE, content=%s WHERE id=%s RETURNING id;""", [content, link['id']])

def request_page(link, session):
	signal.signal(signal.SIGALRM, alarm_handler)
	signal.alarm(10)
	try:
		# print("Now entering " + link['point_b'])
		response = session.get(link['point_b'])
		return response
	except TimeOutException as e:
		run_sql("""UPDATE razorback_link SET visited=True WHERE point_b=%s AND point_a_id=%s RETURNING id;""", [link['point_b'], link['point_a_id']])
	except Exception as e:
		print(str(e))
		return

def get_first_available_link():
	link = run_sql("""SELECT * FROM razorback_link WHERE visited=FALSE AND taken=FALSE FETCH FIRST ROW ONLY;""")
	if link:
		link = {
			'id': link[0],
			'point_b': link[1],
			'visited': link[2],
			'point_a_id': link[3],
			'content': link[4],
			'taken': link[5]
		}
	return link

def claim_link(link):
	run_sql("""UPDATE razorback_link SET taken=TRUE WHERE id=%s RETURNING id;""", [link['id']])

def unclaim_link(link):
	run_sql("""UPDATE razorback_link SET taken=FALSE WHERE id=%s RETURNING id;""", [link['id']])

def surf_link(link, session):
	try:
		start = time.time()
		response = request_page(link, session)
		print(f"{time.time() - start} seconds for requesting {link['point_b']}")

		content = response.content
		new_urls = get_urls_from_page(link['point_b'], content)
		new_links = links_from_urls(link, new_urls)

		save_link_list(new_links)
		update_visited_link(link, content)

	except Exception as e:
		print(str(e))

def surf_next_link(session):
	link = get_first_available_link()
	if link:
		claim_link(link)
		surf_link(link, session)
		unclaim_link(link)