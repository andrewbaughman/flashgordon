import psycopg2

def run_sql(sql, params=None):
	""" Run any sql string on the lightning_db database """
	conn = None
	ret = None
	try:
		conn = psycopg2.connect(dbname="lightning_db", user="andrew", password="password")
		cur = conn.cursor()
		cur.execute(sql, params)
		ret = cur.fetchone()
		conn.commit()
		cur.close()
	except (Exception, psycopg2.DatabaseError) as e:
		print(str(e))
	finally:
		if conn is not None:
			conn.close()
	return ret

def save_link_list(link_list):
	"""
	Insert many Links into the the Link table
	"""
	sql = """INSERT INTO razorback_link(point_b, visited, point_a_id, taken) VALUES(%s,%s,%s,%s)"""
	conn = None
	try:
		conn = psycopg2.connect(dbname="lightning_db", user="andrew", password="password")
		cur = conn.cursor()
		cur.executemany(sql, link_list)
		conn.commit()
		cur.close()
	except (Exception, psycopg2.DatabaseError) as e:
		print(str(e))
	finally:
		if conn is not None:
			conn.close()