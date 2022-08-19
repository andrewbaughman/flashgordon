from db_utils import *
from surfing import *
import requests

query_count_available_links = """SELECT COUNT(*) FROM razorback_link WHERE visited=False AND taken=False;"""

def plant_seed_link():
	print("There are no links in the database.")
	url = ""
	while not 'http://' in url and not 'https://' in url:
		url = input("Provide seed link:")
		if not (url[0:7] == 'http://' or url[0:8] == 'https://'):
			print("NOTE: provide in http:// or https:// form")
		else:
			run_sql("""INSERT INTO razorback_link(point_b, visited, point_a_id, taken) VALUES(%s,FALSE,NULL,FALSE) RETURNING id;""", [url])

if __name__ == '__main__':
	if (run_sql("""SELECT COUNT(*) FROM razorback_link;""")[0] == 0):
		plant_seed_link()
	else:
		print("resuming crawl...")

	with requests.Session() as session:
		unvisited_link_count = run_sql(query_count_available_links)[0]
		while unvisited_link_count > 0:
			surf_next_link(session)
			unvisited_link_count = run_sql(query_count_available_links)[0]