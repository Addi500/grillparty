import sqlite3 as sql
import os

std_path = "database.db"

###Grundfunktionen:

def establish_connection(sql_filepath=std_path):
	connection = sql.connect(sql_filepath, check_same_thread=False)
	cursor = connection.cursor()
	return connection, cursor

def write_to_db(connection, cursor, sql_script, parameters=[]):
	try:
		cursor.execute(sql_script, parameters)
		connection.commit()
	except:
		### ERROR HANDLING
		pass

def initial_db(name=std_path):
	if os.path.exists(name):
		#do more stuff
		print("Datei bereits vorhanden")
	else:
		conn, cur = establish_connection(name)
		initialization_script = """
				CREATE TABLE users (
				mailaddress TEXT NOT NULL PRIMARY KEY,
				name TEXT NOT NULL,
				password TEXT NOT NULL);
				"""
		write_to_db(conn, cur, initialization_script)

		initialization_script = """
				CREATE TABLE parties (
				id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
				title TEXT NOT NULL,
				date TEXT NOT NULL,
				time TEXT NOT NULL,
				address TEXT NOT NULL,
				owner TEXT NOT NULL,
				FOREIGN KEY (owner) REFERENCES users(mailaddress));
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
				FOREIGN KEY (party_id) REFERENCES parties(id),
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

###Insert-Funktionen

def insert_into_users(conn, cur, mailaddress, name, password):
	script = """
	INSERT INTO users VALUES(?,?,?);
	"""
	parameters = [mailaddress, name, password]
	write_to_db(conn, cur, script, parameters)

def insert_into_parties(conn, cur, title, date, time, address, owner):

	#generate id!!!!
	
	#cur.execute("SELECT MAX(id) FROM parties")
	#id = cur.fetchone()[0] + 1

	script = """
	INSERT INTO parties (title, date, time, address, owner) VALUES (?,?,?,?,?);
	"""
	parameters = [title, date, time, address, owner]
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

###Check- und Select-Funktionen

def friend_request(conn, cur, requesting_user, requested_user, operation):
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
	else:
		print("wrong operation")

def check_for_friend_requests(conn, cur, user, operation):
	"""
	checks, if there are new friend requests
	returned tupel:
	0: friend mail (id)
	1: friend name

	operation Arg: "my_requests" or "foreign_requests"
	"""
	if operation == "my_requests":
		script = """
		SELECT users.name, friend2_mail
		FROM friends
		INNER JOIN users on users.mailaddress = friends.friend2_mail
		WHERE friend2_mail NOT IN
			(SELECT friend1_mail
			FROM friends
			WHERE friend2_mail = ?)
		AND friend1_mail = ?;
		"""
		parameters = [user, user]
		cur.execute(script, parameters)
		results = cur.fetchall()
		return results

	elif operation == "foreign_requests":
		script = """
		SELECT users.name, friend1_mail
		FROM friends
		INNER JOIN users on users.mailaddress = friends.friend1_mail
		WHERE friend1_mail IN
			(SELECT friend1_mail
			FROM friends
			WHERE friend2_mail = ?)
		AND NOT friend1_mail IN
			(SELECT friend2_mail
			FROM friends
			WHERE friend1_mail = ?);
		"""
		parameters = [user, user]
		cur.execute(script, parameters)
		results = cur.fetchall()
		return results
	else:
		print("wrong operation")

def view_party(conn, cur, party):
	script = """
	SELECT *
	FROM parties
	WHERE id = ?;
	"""
	parameters = [party]
	cur.execute(script, parameters)
	results = cur.fetchall()
	return results

def select_parties(conn, cur, user, type):
	"""
	returns List of all (type: own/foreign and accepted) parties with all attributes in following order
	id, title, date, time, address, owner

	TODO: nur kommende partys anzeigen/filtermöglichkeit?
	"""
	script = ""
	if type == "own":
		script = """
		SELECT *
		FROM parties
		WHERE owner = ?
		"""		
		parameters = [user]
	elif type == "foreign":
		script = """
		SELECT *
		FROM parties
		WHERE id IN (SELECT party_id FROM participants WHERE participant_mail = ? AND accepted = 1)
		AND owner != ?
		"""
		parameters = [user, user]
	else:
		print("wrong operation")

	cur.execute(script, parameters)
	results = cur.fetchall()
	return results

def select_friends(conn, cur, user):
	"""
	Tupel:
	0: friend mail (id)
	1: friend name
	"""
	script = """
	SELECT users.name, friend2_mail
	FROM friends
	INNER JOIN users on users.mailaddress = friends.friend2_mail
	WHERE friend2_mail IN 
		(SELECT friend1_mail
		FROM friends
		WHERE friend2_mail = ?)
	AND friend1_mail = ?;
	"""
	parameters = [user, user]
	cur.execute(script, parameters)
	friends = cur.fetchall()
	return friends

def search_user(conn, cur, begriff):
	
	script = """
	SELECT *
	FROM users
	WHERE name LIKE (?);
	"""

	parameters = [begriff]
	cur.execute(script, parameters)
	results = cur.fetchall()

	return results

def check_login(conn, cur, mailaddress, password):
	try:
		cur.execute("SELECT password FROM users WHERE mailaddress = ?;", [mailaddress])
		pw = cur.fetchone()[0]
		if pw == password:
			return True
		else:
			return False
	except:
		return False

def check_duplicate(conn, cur, table, column, value):
	#https://stackoverflow.com/questions/61896450/check-duplication-when-edit-an-exist-database-field-with-wtforms-custom-validato

	cur.execute("SELECT * FROM ? WHERE ? = ?;", (table, column, value))
	for row in cur:
		if len(cur.fetchone()) == 0:
			return False
		else:
			return True	

def select_open_party_invites(conn, cur, user):
	#returns list of titles, date and address of open invites to parties
	
	script = """
	SELECT id, title, date, address, time, owner
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

###UPDATE-Funktionen

def change_itemlist(conn, cur, party, item, operation, user=None):
	"""
	Arg: operations
	"delete"
	"assign_to"
	"unassign_to"
	"""

	if operation == "delete":
		script = """
		DELETE FROM itemlist
		WHERE party_id = ? AND item = ?
		"""
		parameters = [party, item]
	elif operation == "assign_to":
		script = """
		UPDATE itemlist
		SET brought_by = ?
		WHERE party_id = ? AND item = ?
		"""
		if user == None:
			print("user must not be NULL")
			raise ValueError()
		parameters = [user, party, item]
	elif operation == "unassign_to":
		script = """
		UPDATE itemlist
		SET brought_by = NULL
		WHERE party_id = ? AND item = ?
		"""
		parameters = [party, item]

	cur.execute(script, parameters)
	results = cur.fetchall()
	return results