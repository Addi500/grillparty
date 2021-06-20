
from datetime import date
from re import UNICODE
import sqlite3
from sqlite3.dbapi2 import Time
from flask import Flask, render_template, request, redirect
from flask.globals import session
from flask.helpers import url_for
from flask_wtf import FlaskForm
from werkzeug.wrappers import AcceptMixin
from wtforms import widgets
from wtforms.fields import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.fields.core import RadioField, SelectMultipleField
from wtforms.fields.html5 import DateField, SearchField
from wtforms.validators import Email, InputRequired, data_required, email, equal_to, length
from db_connection import *
from wtforms_components import TimeField
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user


app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'secretKeyForCookieGeneration'

db_name = "dbrun4.db"
initial_db(db_name)
conn, cur = establish_connection(db_name)

current_user = ""


#Klasse für Registrierung
class Registrate(FlaskForm):
    User = StringField(label="Username", validators=[InputRequired(), length(min=1, max=10, message='Username darf 1-10 Zeichen enthalten')])
    mailaddress = StringField(label="Mail-Adresse ", validators=[InputRequired(), Email(message='Bitte eine gültige E-mailadresse eingeben.')])
    password = PasswordField(label="Passwort", validators=[InputRequired()]) 
    confirm = PasswordField(label="Passwortwiederholung", validators=[InputRequired(), equal_to('password', message='Passwörter stimmen nicht überein.')])
    submit = SubmitField("Registrieren")
#Einspeisen in die Datenbank! Validierung nach Abgleich mit DB!

#Klasse für Anmeldung
class Login(FlaskForm):
    mailaddress = StringField(label="Mail-Adresse ", validators= [Email(message='Bitte eine gültige E-mailadresse eingeben.')])
    password = PasswordField(label="Passwort")
    submit = SubmitField("Anmelden")
#Abgleich mit Datenbank, Fehlermeldungen (Userdaten nicht vorhanden) einbauen

#Klasse zum Anlegen einer neuen Veranstaltung
class NewEvent(FlaskForm):
    title = StringField(label="Titel ",validators=[InputRequired()])
    date = DateField(label="Datum", default = date.today(), validators=[InputRequired()])
    time = TimeField(label="Uhrzeit", validators=[InputRequired()])
    address = TextAreaField(label="Ort",validators=[InputRequired()])
    #Teilnehmer = SearchField (label="Teilnehmer tbd")
    submit = SubmitField("Erstellen")


class AddFriend(FlaskForm):
    user = SearchField()
    submit = SubmitField("Suchen")

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()
    
class itemlist(FlaskForm):
    #itemlist = aus DB ziehen
    #check = MultiCheckboxField('label', choices=itemlist)
    #https://gist.github.com/doobeh/4667330
    submit = SubmitField("Absenden")
 

@app.route('/')
def index():
    return render_template('start.html')

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/datenschutz')
def datenschutz():
    return render_template('datenschutz.html')

@app.route("/registrate", methods=["GET","POST"])
def registrate():
    form = Registrate()
    if form.validate_on_submit():
        session._get_current_object.__name__
        session["username"] = form.User.data
        session["user"] = form.mailaddress.data
        session["password"] = form.password.data
        print("if ")
        insert_into_users(conn, cur, session["user"], session["username"], session["password"])
        return render_template("registrate_success.html")
    return render_template("registrate.html", form=form)

    #Button zu Anmeldung in die html registrate-success einbauen

@app.route("/login", methods=["GET","POST"])
def login():
    form = Login()
    session['logged_in']=False
            
    if form.validate_on_submit():
        session._get_current_object.__name__
        
        session["user"] = form.mailaddress.data
        session["password"] = form.password.data
        
        print("if ")
        if check_login(conn, cur, session["user"], session["password"]):
            print("correct pw")
            
            session['logged_in']=True 
            return redirect("/dashboard")
        else:
            print("wrong pw")
            #falsches Passwort
            pass

    return render_template("login.html", form=form)

@app.route("/newevent", methods= ["GET", "POST"])
#https://tutorial101.blogspot.com/2020/11/python-flask-add-remove-input-fields.html
#genutzte Vorlage für Zutatenliste - SQL Speicherung auch vorhanden 
def newevent():
    form = NewEvent()
   
    user = session["user"]
    friends = select_friends(conn, cur, user)
    print(friends)

    if form.validate_on_submit():

        session._get_current_object.__name__
        session["title"] = form.title.data
        session["date"] = form.date.data
        session["time"] = str(form.time.data)
        session["address"] = form.address.data
        #session["Teilnehmer"] = form.Teilnehmer.data
        session["itemlist"] = request.form.getlist('field[]')
        print("itemliste: ", session["itemlist"])
        teilnehmer = request.form.getlist("info") #ANSATZ; FUNKTIONIERT NOCH NICHT!!!
        print (teilnehmer)
        

        print("if ")
        id = insert_into_parties(conn, cur, session["title"], session["date"], session["time"], session["address"],user)
        for item in session["itemlist"]:
            insert_into_itemlist(conn, cur, id, item) #change to list above
        for participant in session["Teilnehmer"]:
            insert_into_participants(conn, cur, id, participant) #change to list above
        return render_template("dashboard.html")
    return render_template("newevent.html", form=form, friends = friends)

@app.route("/dashboard", methods=['POST', 'GET'])
def dashboard():
    session._get_current_object.__name__
    user = session["user"]
    own_parties = select_parties(conn, cur, user, "own")
    foreign_parties = select_parties(conn, cur, user, "foreign")
    print(own_parties)

    if request.method == "POST":
        
        Submit = request.form.get("submit")
        
        print(Submit)
        forward_message = "Moving Forward..."
        #party_info = view_party(conn, cur, party_id)
        #return render_template('bearbeiten.html', forward_message=forward_message,own_parties=own_parties, Submit=Submit)
        return redirect(url_for('bearbeiten', pid=Submit))
    

    return render_template("dashboard.html", foreign_parties=foreign_parties, own_parties=own_parties)   

@app.route("/bearbeiten/<pid>", methods=['POST', 'GET'])
def bearbeiten(pid):
    #pid = party[0] #gibt den Value zurück
    #adriansfkt.getPartynamen(pid) (für dich!, deine Select where Party ID == pid)
    #partyname = adriansfkt.getPartynamen(pid)
    #render_template("bearbeiten.html", partyname = partyname )
    #form=NewEvent()
    
    party = view_party(conn, cur, pid) #Tupel mit den Party Attributen
    print('Party:',party)
    
    items = select_itemlist(conn, cur, pid) #Liste aller Items als Tupel bestehend aus item und brought_by
    print('items:',items)
    print('pid',pid)
    #participant = select muss noch geschrieben werden
    if request.method == "POST":
        #save changes (db funktion tbd)
        print("Submit funktioniert")
        #return redirect(url_for('bearbeiten'))
    
    
    #return "Erfolg"
    return render_template("bearbeiten.html", party=party, items = items)

   # form = itemlist()
   # party_info = view_party(conn, cur, party_id)
       


    #if request.method == 'POST':
    #    session._get_current_object.__name__
    #    if request.form['Acceptinvitation'] == '0':
    #        print("1")
    #    elif request.form['Acceptinvitation'] == '2':
    #        print("2")
#@app.route("/Anzeigen/<pid>", methods=['POST', 'GET'])
#def anzeigen(pid):
#    #pid = party[0] gibt den Value zurück
#    #adriansfkt.getPartynamen(pid) (für dich!, deine Select where Party ID == pid)
#    #partyname = adriansfkt.getPartynamen(pid)
#    #render_template("bearbeiten.html", partyname = partyname )
#    party = view_party(conn, cur, pid) #Tupel mit den Party Attributen
#    print(party)
#    items = select_itemlist(conn, cur, pid) #Liste aller Items als Tupel bestehend aus item und brought_by
    
#    print(submit)
    
#    return render_template("anzeigen.html", party=party, items = items)


@app.route('/friends', methods= ["GET", "POST"])
def friends():
    user = session["user"]
    
    friend_requests_to_me = check_for_friend_requests(conn, cur, user, "foreign_requests")
    my_friends = select_friends(conn, cur, user)
    len_friend_requests_to_me = len(friend_requests_to_me)

    if request.method == "POST":
        print("here i am")
        if "Acceptinvitation" in request.form:
            friend_request(conn, cur, user, request.form["Acceptinvitation"],"accept")
        elif "Declineinvitation" in request.form:
            friend_request(conn, cur, user, request.form["Declineinvitation"],"deny")
        elif "delete_friend" in request.form:
            friend_request(conn, cur, user, request.form["delete_friend"],"delete")
        
        friends = select_friends(conn, cur, user)
       
    return render_template('friends.html', friend_requests_to_me=friend_requests_to_me, my_friends=my_friends, len_friend_requests_to_me=len_friend_requests_to_me)

#@app.route(("/party/" + party_id))


@app.route('/addfriend', methods = ["GET", "POST"])
def addfriend():
    form = AddFriend()
    session._get_current_object.__name__  
    session["user_search"] = form.user.data
    suchergebnisse = search_user(conn, cur, session["user_search"])
    print (suchergebnisse)
    
    if form.validate_on_submit():
        session._get_current_object.__name__        
        session["user_search"] = form.user.data
        
        suchergebnisse = search_user(conn, cur, session["user_search"])
        print (suchergebnisse)
        return render_template ('addfriend.html', form=form, suchergebnisse=suchergebnisse)
    return render_template('addfriend.html', form=form, sucherergebnisse = suchergebnisse)
    
#übergibt gesuchten User. Funktion für Buttons fehlt noch
@app.route("/hinzufügen/", methods=['POST'])
def Hinzufügen():
    session._get_current_object.__name__
    #db hinzufügen von Freunden definieren
    #nach Hinzufügen auf addfriend rendern
    return 'Erfolg'

@app.route("/acceptinv/", methods=['POST'])
def AcceptFriends():
    session._get_current_object.__name__
    
    if request.method == 'POST':
        if 'Acceptinvitation' in request.form:
            print("1")
        elif request.form['Acceptinvitation'] == '2':
            print("2")
        
            #insert_into_friends()

    forward_message = "Moving Forward..."

    return render_template('friends.html', forward_message=forward_message);    

@app.route("/declineinv/", methods=['POST'])
def DeclineFriends():
    session._get_current_object.__name__
    
    if request.method == 'POST':
        if request.form['Declineinvitation'] == '0':
            print("1")
        elif request.form['Declineinvitation'] == '2':
            print("2")

    forward_message = "Moving Forward..."

    return render_template('friends.html', forward_message=forward_message);    

@app.route('/invitations', methods=['POST', 'GET'])
def invitations():
    session._get_current_object.__name__
    user = session["user"]
    
    invites = select_open_party_invites(conn, cur, user)
    print(invites)
    if request.method == "POST":
        
        Submit = request.form.get("Submit")
        
        print(Submit)
        forward_message = "Moving Forward..."
        #party_info = view_party(conn, cur, party_id)
        #return render_template('bearbeiten.html', forward_message=forward_message,own_parties=own_parties, Submit=Submit)
        return redirect(url_for('accept', pid=Submit))

    # Abgleich mit db nicht über if sondern anhand Buttonvalue akzeptieren (von 0 auf 1 setzen)
    #Moving forward code

    return render_template('invitations.html', invites = invites)

@app.route("/accept/<pid>", methods=['POST', 'GET'])
def accept(pid):
    session._get_current_object.__name__
    
    script_accept = """
    UPDATE participants
    SET accepted = 1
    WHERE party_id = ? AND participant_mail = ?;
    """
    print("accepted1")
    print(pid, session["user"])
    cur.execute(script_accept, [pid, session["user"]])
    conn.commit()   
    print(pid)

    
    party = view_party(conn, cur, pid) #Tupel mit den Party Attributen
    print(party)
    items = select_itemlist(conn, cur, pid) #Liste aller Items als Tupel bestehend aus item und brought_by
    
    print(items)
    
    #ändern: change_itemlist()
    
    #return 'Erfolg'
    return render_template('anzeigen.html', items = items, party = party)

@app.route("/decline/", methods=['POST'])
def Decline():
    session._get_current_object.__name__

    script_decline = """
    DELETE FROM participants
    WHERE party_id = ? AND participant_mail = ?;
    """
    print("Declined2")
    cur.execute(script_decline, [request.form['Decline'], session["user"]])
    conn.commit()

    forward_message = "Moving Forward..."
    return render_template('dashboard.html', forward_message=forward_message)


@app.route("/logout/", methods=['POST'])
def Logout():
    session._get_current_object.__name__    
    forward_message = "Moving Forward..."
    if request.method == 'POST':
        session['logged_in']=False
        session["address"] = None
        session ['user'] = None
        print("Ich bin ausgeloggt")
        return render_template('start.html')
        
        
    return render_template('dashboard.html', forward_message=forward_message)
    
#keine Klasse bisher angelegt, benötigt Übergabe der Einladungen aus der
#Datenbank, Buttons noch ohne Funktion, Einladungsart (Freunde / Veranstaltung)
# Einladung von: User, bei Veranstaltung komplette Ausgabe der Einladnung, neue form
# für Auswahl der Mitbringsel


if __name__ == '__main__':
    app.run()
    app.run(debug=True)