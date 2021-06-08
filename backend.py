import sqlite3 as sql
import os

std_path = "database.db"

def write_to_db(cursor, connection, sql_script, parameters=[]):
	cursor.execute(sql_script, parameters)
	connection.commit()

def initial_db(name=std_path):
	if os.path.exists(name):
		#do more stuff
		print("Datei bereits vorhanden")
	else:
		conn, cur = establish_connection(name)
		initialization_script = """
				CREATE TABLE users (
				mailaddress TEXT NOT NULL,
				name TEXT NOT NULL,
				password TEXT NOT NULL,
				PRIMARY KEY (mailaddress));
				"""
		write_to_db(cur, conn, initialization_script)

		initialization_script = """
				CREATE TABLE parties (
				id INT NOT NULL,
				title TEXT NOT NULL,
				date TEXT NOT NULL,
				time TEXT NOT NULL,
				address TEXT NOT NULL,
				description TEXT NOT NULL,
				PRIMARY KEY (id));
				"""
		write_to_db(cur, conn, initialization_script)

		initialization_script = """
				CREATE TABLE participants (
				party_id INT NOT NULL,
				participant_mail TEXT NOT NULL,
				FOREIGN KEY (party_id) REFERENCES parties(id),
				FOREIGN KEY (participant_mail) REFERENCES users(mailaddress));
				"""
		write_to_db(cur, conn, initialization_script)

		initialization_script = """
				CREATE TABLE itemlist (
				party_id INT NOT NULL,
				item TEXT NOT NULL,
				PRIMARY KEY (party_id,item));
		"""
		write_to_db(cur, conn, initialization_script)
		#bonus: encrypt passwords. http://blog.dornea.nu/2011/07/28/howto-keep-your-passwords-safe-using-sqlite-and-sqlcipher/

def establish_connection(sql_filepath=std_path):
	connection = sql.connect(sql_filepath, check_same_thread=False)
	cursor = connection.cursor()
	return connection, cursor

def insert_into_users(conn, cur, mailaddress, name, password):
	script = """
	INSERT INTO users VALUES(?,?,?)
	"""
	parameters = [mailaddress, name, password]
	write_to_db(cur, conn, script, parameters)

def insert_into_parties(conn, cur, title, date, time, address, description):

	#generate id!!!!
	#hochzählen oder zufallszahl/hash?
	"""
	hochzählen:
	max of(select all existing ids in db)
	+1
	=id
	
	"""

	id = 0

	script = """
	INSERT INTO parties (?,?,?,?,?,?)
	"""
	parameters = [id, title, date, time, address, description]
	write_to_db(cur, conn, script, parameters)

def insert_into_participants(conn, cur, party_id, participant_mail):
	script = """
	INSERT INTO participants (?,?)
	"""
	parameters = [party_id, participant_mail]
	write_to_db(cur, conn, script, parameters)

def insert_into_itemlist(conn, cur, party_id, item):

	#wie werden die Items übergeben? hier schon for-schleife oder beim aufruf jeweils?

	script = """
	INSERT INTO itemlist (?,?)
	"""
	parameters = [party_id, item]
	write_to_db(cur, conn, script, parameters)

def check_login(conn, cur, mailaddress, password):
	cur.execute("SELECT password FROM users WHERE mailaddress = ?;", (mailaddress,))
	pw = cur.fetchone()[0]
	if pw == password:
		return True
	else:
		return False

def check_duplicate(conn, cur, table, column, value):
	#https://stackoverflow.com/questions/61896450/check-duplication-when-edit-an-exist-database-field-with-wtforms-custom-validato

	cur.execute("SELECT * FROM ? WHERE ? = ?", (table, column, value))
	for row in cur:
		if len(cur.fetchone()) == 0:
			continue
		else:
			return True
	return False
	#wenn leer, nichts vorhanden
	#wenn wert in tupel: duplikat


#if __name__ == "__main__":
#	print("first test")

#	dbname = "test19h.db"

#	conn, cur = establish_connection()