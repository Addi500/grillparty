import sqlite3 as sql
import os
from datetime import date, datetime
import hashlib

std_path = "database.db"

###Grundfunktionen:

def establish_connection(sql_filepath=std_path):
	connection = sql.connect(sql_filepath, check_same_thread=False)
	cursor = connection.cursor()
	print("established Connection to Database ", sql_filepath)
	return connection, cursor

def write_to_db(connection, cursor, sql_script, parameters=[]):
	try:
		cursor.execute(sql_script, parameters)
		connection.commit()
		return cursor.lastrowid
	except:
		### ERROR HANDLING
		print("SQLError")
		raise	

def initial_db(name=std_path):
	if os.path.exists(name):
		#do more stuff
		print("Datei bereits vorhanden")
	else:
		print("...creating new Database")

		conn, cur = establish_connection(name)
		initialization_script = """
				CREATE TABLE users (
				mailaddress TEXT NOT NULL PRIMARY KEY,
				name TEXT NOT NULL,
				password TEXT NOT NULL,
				last_edited TEXT);
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
				last_edited TEXT,
				FOREIGN KEY (owner) REFERENCES users(mailaddress));
				"""
		write_to_db(conn, cur, initialization_script)

		initialization_script = """
				CREATE TABLE participants (
				party_id INT NOT NULL,
				participant_mail TEXT NOT NULL,
				accepted INT NOT NULL,
				last_edited TEXT,
				FOREIGN KEY (party_id) REFERENCES parties(id),
				FOREIGN KEY (participant_mail) REFERENCES users(mailaddress));
				"""
		write_to_db(conn, cur, initialization_script)

		initialization_script = """
				CREATE TABLE itemlist (
				party_id INT NOT NULL,
				item TEXT NOT NULL,
				brought_by TEXT,
				last_edited TEXT,
				FOREIGN KEY (party_id) REFERENCES parties(id),
				FOREIGN KEY (brought_by) REFERENCES users(mailaddress));
		"""
		write_to_db(conn, cur, initialization_script)

		initialization_script = """
				CREATE TABLE friends (
				friend1_mail TEXT NOT NULL,
				friend2_mail TEXT NOT NULL,
				last_edited TEXT,
				PRIMARY KEY (friend1_mail, friend2_mail)
				FOREIGN KEY (friend1_mail) REFERENCES users(mailaddress),
				FOREIGN KEY (friend2_mail) REFERENCES users(mailaddress));
		"""
		write_to_db(conn, cur, initialization_script)

		###trigger für last_edited date
		trigger_script = """
		CREATE TRIGGER last_edited_trigger_friends
         AFTER INSERT
            ON friends
		BEGIN
			UPDATE friends
			   SET last_edited = datetime('now') 
			 WHERE friend1_mail = NEW.friend1_mail AND 
				   friend2_mail = NEW.friend2_mail;
		END;

		CREATE TRIGGER last_edited_trigger_friends_updated
         AFTER UPDATE OF friend1_mail,
                         friend2_mail
            ON friends
		BEGIN
			UPDATE friends
			   SET last_edited = datetime('now') 
			 WHERE friend1_mail = NEW.friend1_mail AND 
				   friend2_mail = NEW.friend2_mail;
		END;



		CREATE TRIGGER last_edited_trigger_itemlist
				 AFTER INSERT
					ON itemlist
		BEGIN
			UPDATE itemlist
			   SET last_edited = datetime('now') 
			 WHERE party_id = NEW.party_id AND 
				   item = NEW.item;
		END;

		CREATE TRIGGER last_edited_trigger_itemlist_updated
         AFTER UPDATE OF party_id,
                         item,
                         brought_by
					ON itemlist
		BEGIN
			UPDATE itemlist
			   SET last_edited = datetime('now') 
			 WHERE party_id = NEW.party_id AND 
				   item = NEW.item;
		END;



		CREATE TRIGGER last_edited_trigger_participants
				 AFTER INSERT
					ON participants
		BEGIN
			UPDATE participants
			   SET last_edited = datetime('now') 
			 WHERE party_id = NEW.party_id AND 
				   participant_mail = NEW.participant_mail;
		END;

		CREATE TRIGGER last_edited_trigger_participants_updated
         AFTER UPDATE OF party_id,
                         participant_mail,
                         accepted
            ON participants
		BEGIN
			UPDATE participants
			   SET last_edited = datetime('now') 
			 WHERE party_id = NEW.party_id AND 
				   participant_mail = NEW.participant_mail;
		END;



		CREATE TRIGGER last_edited_trigger_parties
				 AFTER INSERT
					ON parties
		BEGIN
			UPDATE parties
			   SET last_edited = datetime('now') 
			 WHERE id = NEW.id;
		END;

		CREATE TRIGGER last_edited_trigger_parties_updated
         AFTER UPDATE OF id,
                         title,
                         date,
                         time,
                         address,
                         owner
            ON parties
		BEGIN
			UPDATE parties
			   SET last_edited = datetime('now') 
			 WHERE id = NEW.id;
		END;



		CREATE TRIGGER last_edited_trigger_users
				 AFTER INSERT
					ON users
		BEGIN
			UPDATE users
			   SET last_edited = datetime('now') 
			 WHERE mailaddress = NEW.mailaddress;
		END;

		CREATE TRIGGER last_edited_trigger_users_updated
         AFTER UPDATE OF mailaddress,
                         name,
                         password
            ON users
		BEGIN
			UPDATE users
			   SET last_edited = datetime('now') 
			 WHERE mailaddress = NEW.mailaddress;
		END;

		"""
		cur.executescript(trigger_script)

		print("created new Database ", name)
		#bonus: encrypt passwords. http://blog.dornea.nu/2011/07/28/howto-keep-your-passwords-safe-using-sqlite-and-sqlcipher/

###Insert-Funktionen

def insert_into_users(conn, cur, mailaddress, name, password):
	encrypted_pw = hashlib.sha256(password.encode('utf-8')).hexdigest()
	print(encrypted_pw)
	
	script = """
	INSERT INTO users (mailaddress, name, password) VALUES (?,?,?);
	"""
	parameters = [mailaddress, name, encrypted_pw]
	write_to_db(conn, cur, script, parameters)

def insert_into_parties(conn, cur, title, date, time, address, owner):
	script = """
	INSERT INTO parties (id, title, date, time, address, owner) VALUES (NULL,?,?,?,?,?);
	"""
	parameters = [title, date, time, address, owner]
	id = write_to_db(conn, cur, script, parameters)
	
	#script = """
	#INSERT INTO participants (party_id, participant_mail, accepted) VALUES (?,?,?);
	#"""
	#parameters = [party_id, owner, 1]
	#write_to_db(conn, cur, script, parameters)

	return id

def insert_into_participants(conn, cur, party_id, participant_mail):
	script = """
	INSERT INTO participants (party_id, participant_mail, accepted) VALUES (?,?,?);
	"""
	parameters = [party_id, participant_mail, 0]
	write_to_db(conn, cur, script, parameters)

def insert_into_itemlist(conn, cur, party_id, item):

	#wie werden die Items übergeben? hier schon for-schleife oder beim aufruf jeweils?

	script = """
	INSERT INTO itemlist (party_id, item, brought_by) VALUES (?,?,?);
	"""
	parameters = [party_id, item, None]
	write_to_db(conn, cur, script, parameters)

def insert_into_friends(conn, cur, friend1, friend2):
	script = """
	INSERT INTO friends (friend1_mail, friend2_mail) VALUES (?,?);
	"""
	parameters = [friend1, friend2]
	write_to_db(conn, cur, script, parameters)

###Check- und Select-Funktionen

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
	results = cur.fetchone()
	results = list(results)
	results[2] = readable_date_time(results[2], "date")
	results[3] = readable_date_time(results[3], "time")
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
		SELECT parties.*, users.name
		FROM parties
		INNER JOIN users on users.mailaddress = parties.owner
		WHERE owner = ?
		"""		
		parameters = [user]
	elif type == "foreign":
		script = """
		SELECT parties.*, users.name
		FROM parties
		INNER JOIN users on users.mailaddress = parties.owner
		WHERE id IN (SELECT party_id FROM participants WHERE participant_mail = ? AND accepted = 1)
		AND owner != ?
		"""
		parameters = [user, user]
	else:
		print("wrong operation")

	cur.execute(script, parameters)
	results = cur.fetchall()
	for i in range(len(results)):
		results[i] = list(results[i])
		results[i][2] = readable_date_time(results[i][2], "date")
		results[i][3] = readable_date_time(results[i][3], "time")
	if len(results) == 0:
		results = 0

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

def search_user(conn, cur, begriff, searching_user):
	results =[]
	begriff = "%"+begriff+"%"
	print (begriff)

	script = """
	SELECT mailaddress, name
	FROM users
	WHERE (name LIKE (?))
	AND mailaddress NOT IN (SELECT friend2_mail FROM friends WHERE friend1_mail = ?)
	AND mailaddress NOT IN (?);
	"""

	parameters = [begriff, searching_user, searching_user]
	cur.execute(script, parameters)
	results = cur.fetchall()

	if len(results) == 0:
		results = 0

	return results

def check_login(conn, cur, mailaddress, password):
	cur.execute("SELECT password FROM users WHERE mailaddress = ?;", [mailaddress])
	encrypted_pw = hashlib.sha256(password.encode('utf-8')).hexdigest()
	try:
		pw = cur.fetchone()[0]

		#if cur.rowcount <= 0 :
		#	print("hierrrr")
		#	return False
		#else:
		if pw == encrypted_pw:
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
	SELECT id, title, date, time, address, owner, users.name
	FROM parties
	INNER JOIN users on users.mailaddress = parties.owner
	WHERE parties.id
	IN (SELECT party_id FROM participants WHERE participant_mail = ? AND accepted = 0);
	"""

	parameters = [user]
	cur.execute(script, parameters)
	results = cur.fetchall()
	for party in results:
		party = list(party)
		party[2] = readable_date_time(party[2], "date")
		party[3] = readable_date_time(party[3], "time")
	if len(results) == 0:
		results = 0
		
	return results

def select_itemlist(conn, cur, party):
	#returns list of all items of party with name who brings it

	script = """
	SELECT party_id, item, brought_by, users.name
	FROM itemlist
	LEFT JOIN users ON users.mailaddress = itemlist.brought_by
	WHERE party_id = ?;
	"""
	parameters = [party]
	cur.execute(script, parameters)
	results = cur.fetchall()
	for i in range(len(results)):
		results[i]=list(results[i])
		if results[i][2] == None:
			results[i][2] = 0
			print(results)
	return results

def select_participants(conn, cur, pid, type):
	"""
	type options:
	"all"
	"accepted"
	"open"
	"""
	if type == "all":
		script = """
		SELECT participants.party_id, participants.participant_mail, participants.accepted, users.name
		FROM participants
		INNER JOIN users ON users.mailaddress = participants.participant_mail
		WHERE party_id = ?;
		"""
	elif type == "accepted":
		script = """
		SELECT participants.party_id, participants.participant_mail, participants.accepted, users.name
		FROM participants
		INNER JOIN users ON users.mailaddress = participants.participant_mail
		WHERE party_id = ? AND accepted = 1;
		"""
	elif type == "open":
		script = """
		SELECT participants.party_id, participants.participant_mail, participants.accepted, users.name
		FROM participants
		INNER JOIN users ON users.mailaddress = participants.participant_mail
		WHERE party_id = ? AND accepted = 0;
		"""
	else:
		print("wrong type")
		raise

	parameters = [pid]
	cur.execute(script, parameters)
	results = cur.fetchall()
	return results

def select_guests(conn, cur, pid):
	script = """
	SELECT participants.party_id, participants.participant_mail, participants.accepted, users.name, itemlist.item, itemlist.brought_by
	FROM participants
	INNER JOIN users ON users.mailaddress = participants.participant_mail
	LEFT JOIN itemlist ON itemlist.brought_by = participants.participant_mail
	WHERE participants.party_id = ?
	"""
	parameters = [pid]
	cur.execute(script, parameters)
	results = cur.fetchall()
	for i in range(len(results)):
		pass
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

	write_to_db(conn, cur, script, parameters)

def friend_request(conn, cur, user1, user2, operation):
	"""
	Arg: operation
	"request" : someone asks for a new friendship
	"accept" : user2 allows new friendship
	"deny" : asked user denies
	"delete" : delete friendship on both sides
	first initiator is always "user1"
	"""

	if operation == "request":
		insert_into_friends(conn, cur, user1, user2)
	elif operation == "accept":
		insert_into_friends(conn, cur, user1, user2)
	elif operation == "deny":
		script = """
		DELETE FROM friends
		WHERE friend1_mail = ? AND friend2_mail = ?;
		"""
		parameters = [user2, user1]

		cur.execute(script, parameters)
		conn.commit()
		print("commited", conn)
	elif operation == "delete":
		script = """
		DELETE FROM friends
		WHERE friend1_mail = ? AND friend2_mail = ?;
		"""

		parameters = [user1, user2]
		cur.execute(script, parameters)
		conn.commit()

		script = """
		DELETE FROM friends
		WHERE friend1_mail = ? AND friend2_mail = ?;
		"""
		parameters = [user2, user1]
		cur.execute(script, parameters)
		conn.commit()

	else:
		print("wrong operation")

def update_party(conn, cur, pid, value, operation):
	"""
	operations:
	"title"
	"date"
	"time"
	"address"
	"""
	if operation == "title":
		script = """
		UPDATE parties
		SET title = ?
		WHERE id = ?;
		"""		
	elif operation == "date":
		script = """
		UPDATE parties
		SET date = ?
		WHERE id = ?;
		"""
	elif operation == "time":
		script = """
		UPDATE parties
		SET time = ?
		WHERE id = ?;
		"""
	elif operation == "address":
		script = """
		UPDATE parties
		SET address = ?
		WHERE id = ?;
		"""
	else:
		print("wrong operation")

	parameters = [value, pid]
	write_to_db(conn, cur, script, parameters)

def change_participants(conn, cur, pid, user, operation):
	"""
	operations:
	"new_participant"
	"accept"
	"delete"
	"""
	
	if operation == "new_participant":
		script = """
		INSERT INTO participants (party_id, participant_mail, accepted)
		VALUES (?,?,0);
		"""
	elif operation == "accept":
		script = """
		UPDATE participants
		SET accepted = 0
		WHERE party_id = ? AND participant_mail = ?;
		"""
	elif operation == "delete":
		script = """
		DELETE FROM participants
		WHERE party_id = ? AND participant_mail = ?;
		"""
	else:
		print("wrong operation")

	parameters = [pid, user]
	write_to_db(conn, cur, script, parameters)

def change_user(conn, cur, user, value, operation):
	"""
	operations:
	"name"
	"pw"
	"""
	if operation == "name":
		script = """
		UPDATE users
		SET name = ?
		WHERE mailadress = ?
		"""
	elif operation == "pw":
		script = """
		UPDATE users
		SET password = ?
		WHERE mailadress = ?
		"""
	else:
		print("wrong operation")
		raise
	parameters = [value, user]
	write_to_db(conn, cur, script, parameters)

###util-funktionen

def readable_date_time(input, type):
	"""
	type: "date" or "time"
	"""
	if type == "date":
		datetimeobject = datetime.strptime(input, '%Y-%m-%d')
		return datetimeobject.strftime("%d.%m.%Y")
	elif type == "time":
		datetimeobject = datetime.strptime(input, '%H:%M:%S')
		return datetimeobject.strftime("%H:%M")
	else:
		print("wrong type")