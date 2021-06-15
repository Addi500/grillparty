import sqlite3 as sql
import os


"""
TODO:

- SQL ERROR HANDLING
"""



std_path = "database.db"

def write_to_db(connection, cursor, sql_script, parameters=[]):
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
		write_to_db(conn, cur, initialization_script)

		initialization_script = """
				CREATE TABLE parties (
				id INT NOT NULL,
				title TEXT NOT NULL,
				date TEXT NOT NULL,
				time TEXT NOT NULL,
				address TEXT NOT NULL,
				owner TEXT NOT NULL
				PRIMARY KEY (id),
				FOREIGN KEY (owner) REFERNCES users(mailaddress));
				"""
		write_to_db(conn, cur, initialization_script)

		initialization_script = """
				CREATE TABLE participants (
				party_id INT NOT NULL,
				participant_mail TEXT NOT NULL,
				accepted INT NOT NULL,
				FOREIGN KEY (party_id) REFERENCES parties(id),
				FOREIGN KEY (participant_mail) REFERENCES users(mailaddress));
				"""
		write_to_db(conn, cur, initialization_script)

		initialization_script = """
				CREATE TABLE itemlist (
				party_id INT NOT NULL,
				item TEXT NOT NULL,
				brought_by TEXT,
				PRIMARY KEY (party_id,item)
				FOREIGN KEY (brought_by) REFERENCES users(mailaddress));
		"""
		write_to_db(conn, cur, initialization_script)

		initialization_script = """
				CREATE TABLE friends (
				friend1_mail TEXT NOT NULL,
				friend2_mail TEXT NOT NULL,
				FOREIGN KEY (friend1_mail) REFERENCES users(mailaddress),
				FOREIGN KEY (friend2_mail) REFERENCES users(mailaddress));
		"""
		write_to_db(conn, cur, initialization_script)
		#bonus: encrypt passwords. http://blog.dornea.nu/2011/07/28/howto-keep-your-passwords-safe-using-sqlite-and-sqlcipher/

def establish_connection(sql_filepath=std_path):
	connection = sql.connect(sql_filepath, check_same_thread=False)
	cursor = connection.cursor()
	return connection, cursor

def insert_into_users(conn, cur, mailaddress, name, password):
	script = """
	INSERT INTO users VALUES(?,?,?);
	"""
	parameters = [mailaddress, name, password]
	write_to_db(conn, cur, script, parameters)

def insert_into_parties(conn, cur, title, date, time, address, owner):

	#generate id!!!!
	#hochzählen oder zufallszahl/hash?
	"""
	hochzählen:
	max of(select all existing ids in db)
	+1
	=id
	
	"""

	cur.execute("SELECT MAX(id) FROM parties")
	id = cur.fetchone()[0] + 1

	script = """
	INSERT INTO parties VALUES (?,?,?,?,?,?);
	"""
	parameters = [id, title, date, time, address, owner]
	write_to_db(conn, cur, script, parameters)
	return id

def insert_into_participants(conn, cur, party_id, participant_mail):
	script = """
	INSERT INTO participants VALUES (?,?,?);
	"""
	parameters = [party_id, participant_mail, 0]
	write_to_db(conn, cur, script, parameters)

def insert_into_itemlist(conn, cur, party_id, item):

	#wie werden die Items übergeben? hier schon for-schleife oder beim aufruf jeweils?

	script = """
	INSERT INTO itemlist VALUES (?,?,?);
	"""
	parameters = [party_id, item, None]
	write_to_db(conn, cur, script, parameters)

def insert_into_friends(conn, cur, friend1, friend2):
	script = """
	INSERT INTO friends VALUES (?,?);
	"""
	parameters = [friend1, friend2]
	write_to_db(conn, cur, script, parameters)

def new_friend_request(conn, cur, requesting_user, requested_user, operation):
	"""
	Arg: operation
	"request" : someone asks for a new friendship
	"accept" : requested_user allows new friendship
	"deny" : asked user denies
	first initiator is always "requesting_user"
	"""

	if operation == "request":
		insert_into_friends(conn, cur, requesting_user, requested_user)
	elif operation == "accept":
		insert_into_friends(conn, cur, requested_user, requesting_user)
	elif operation == "deny":
		script = """
		DELETE FROM friends
		WHERE friend1 = ? AND friend2 = ?;
		"""
		parameters = [requesting_user, requested_user]

		cur.execute(script, parameters)
		conn.commit()

def check_for_friend_requests(conn, cur, user):
	"""
	checks, if there are new friend requests
	"""

	script = """
	CASE (S
	WH
	SELECT friend1
	FROM friends
	WHERE friend2 = ?;
	"""

def search(conn, cur, table, begriff):
	
	script = """
	SELECT *
	FROM ?
	WHERE name = ?;
	"""

	parameters = [table, begriff]
	cur.execute(script, parameters)
	results = cur.fetchall()

	return results

	###db abfrage
	###returns

def check_login(conn, cur, mailaddress, password):
	cur.execute("SELECT password FROM users WHERE mailaddress = ?;", (mailaddress,))
	pw = cur.fetchone()[0]
	if pw == password:
		return True
	else:
		return False

def check_duplicate(conn, cur, table, column, value):
	#https://stackoverflow.com/questions/61896450/check-duplication-when-edit-an-exist-database-field-with-wtforms-custom-validato

	cur.execute("SELECT * FROM ? WHERE ? = ?;", (table, column, value))
	for row in cur:
		if len(cur.fetchone()) == 0:
			continue
		else:
			return True
	return False

def select_parties_of_user(conn, cur, user):
	#only returns own parties right now
	
	script = """
	SELECT title, date, address
	FROM parties
	WHERE owner = ?;
	"""
	parameters=[user]
	cur.execute(script, parameters)
	results = cur.fetchall()

	return results

def select_open_party_invites(conn, cur, user):
	#returns list of titles, date and address of open invites to parties
	
	script = """
	SELECT title, date, address
	FROM parties
	WHERE parties.id
	IN (SELECT party_id FROM participants WHERE participant_mail = ? AND accepted = 0);
	"""

	parameters = [user]
	cur.execute(script, parameters)
	results = cur.fetchall()
	return results

def select_itemlist(conn, cur, party):
	#returns list of all items of party with name who brings it

	script = """
	SELECT item, brought_by
	FROM itemlist
	WHERE party_id = ?;
	"""
	parameters = [party]
	cur.execute(script, parameters)
	results = cur.fetchall()
	return results

###strukturänderungen db (neue spalte bei participants, ob zugesagt)


	#wenn leer, nichts vorhanden
	#wenn wert in tupel: duplikat


#if __name__ == "__main__":
#	print("first test")

#	dbname = "test19h.db"

#	conn, cur = establish_connection()