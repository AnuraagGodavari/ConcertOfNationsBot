import mysql.connector as mariadb, sys, os
from dotenv import load_dotenv

mariadb_connection = None

def fetch_assoc(cursor):
	return dict(zip(cursor.column_names, cursor.fetchone()))

def getdb():
	"""
	Returns a connection to a MySQL/MariaDB database.
	Returns:
		mariadb_connection: The result of mariadb.connect(), either saved earlier or newly connected.
	"""
	
	global mariadb_connection
	
	if not mariadb_connection:
		
		load_dotenv()
		db_user = os.getenv('DB_USER')
		db_pass = os.getenv('DB_PASS')
		db_host = os.getenv('DB_HOST')
		db_port = os.getenv('DB_PORT')
		db_name = os.getenv('DB_DATABASE')

		try:
			connection = mariadb.connect(user=db_user, password=db_pass, host=db_host, port=db_port, database=db_name)
			mariadb_connection = connection

		except mariadb.Error as e:
			print(f"Error connecting to MariaDB Platform: {e}")
			return

	return mariadb_connection

