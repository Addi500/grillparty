
from datetime import date
from flask import Flask, render_template, request, redirect, flash
from flask.globals import session
from flask.helpers import url_for
from flask_wtf import FlaskForm
from wtforms.fields import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.fields.html5 import DateField, SearchField
from wtforms.validators import Email, InputRequired, equal_to, length
from db_connection import *
from wtforms_components import TimeField, DateRange


###Basics

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'secretKeyForCookieGeneration'

db_name = "dbrun6.db"
initial_db(db_name)
conn, cur = establish_connection(db_name)


###Klassen

class Registrate(FlaskForm): #Klasse für Registrierung
    User = StringField(label="Username", validators=[InputRequired(), length(min=1, max=10, message='Username darf 1-10 Zeichen enthalten')])
    mailaddress = StringField(label="Mail-Adresse ", validators=[InputRequired(), Email(message='Bitte eine gültige E-mailadresse eingeben.')])
    password = PasswordField(label="Passwort", validators=[InputRequired()]) 
    confirm = PasswordField(label="Passwortwiederholung", validators=[InputRequired(), equal_to('password', message='Passwörter stimmen nicht überein.')])
    submit = SubmitField("Registrieren")

class Login(FlaskForm): #Klasse für Anmeldung
    mailaddress = StringField(label="Mail-Adresse ", validators= [Email(message='Ungültige E-Mailadresse.')])
    password = PasswordField(label="Passwort")
    submit = SubmitField("Anmelden")

class NewEvent(FlaskForm): #Klasse zum Anlegen einer neuen Veranstaltung
    title = StringField(label="Titel", validators=[InputRequired()])
    date = DateField(label="Datum", validators=[DateRange(min=date.today())], default = date.today())
    time = TimeField(label="Uhrzeit", validators=[InputRequired()])
    address = TextAreaField(label="Ort", validators=[InputRequired()])
    submit = SubmitField("Erstellen")

class AddFriend(FlaskForm):
    user = SearchField()
    submit = SubmitField("Suchen")


#App-Routen

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
            #falsches Passwort
            print("wrong pw")
            flash("Falsche Email oder falsches Passwort")
            return redirect("/login")

    return render_template("login.html", form=form)

@app.route("/newevent", methods= ["GET", "POST"])
def newevent():
    form = NewEvent()
   
    user = session["user"]
    friends = select_friends(conn, cur, user)
    print(friends)

    if form.validate_on_submit():
        session._get_current_object.__name__
        session["title"] = form.title.data
        session["date"] = form.date.data
        session["time"] = str(form.time.data) #Konvertierung in String, sonst Json Fehler
        session["address"] = form.address.data
        session["Teilnehmer"] = request.form.getlist("checkbox")
        session["itemlist"] = request.form.getlist('field[]')              
               
        id = insert_into_parties(conn, cur, session["title"], session["date"], session["time"], session["address"],user)
        #owner als participant hinzufügen
        insert_into_participants(conn, cur, id, user)
        change_participants(conn, cur, id, user, "accept")

        for item in session["itemlist"]:
            insert_into_itemlist(conn, cur, id, item)
        for participant in session["Teilnehmer"]:
            print(participant)
            insert_into_participants(conn, cur, id, participant)
        return redirect(url_for("dashboard"))
    return render_template("newevent.html", form=form, friends = friends)

@app.route("/dashboard", methods=['POST', 'GET'])
def dashboard():
    session._get_current_object.__name__
    user = session["user"]
    own_parties = select_parties(conn, cur, user, "own")
    foreign_parties = select_parties(conn, cur, user, "foreign")
    try:
        for i in range(len(foreign_parties)):
            guest_items = select_guests_items(conn, cur, foreign_parties[i][0], "one", user)
            foreign_parties[i].append(guest_items[1])
    except:
        print("Keine Items vorhanden")
    if request.method == "POST":        
        Submit = request.form.get("submit")                
        return redirect(url_for('bearbeiten', pid=Submit))   

    return render_template("dashboard.html", foreign_parties=foreign_parties, own_parties=own_parties)   

@app.route("/bearbeiten/<pid>", methods=['POST', 'GET'])
def bearbeiten(pid):    
    party = view_party(conn, cur, pid) #Tupel mit den Party Attributen    
    items = select_itemlist(conn, cur, pid, "all") #Liste aller Items als Tupel bestehend aus item und brought_by      
    participants = select_participants(conn, cur, pid, "all")
    guests = select_guests_items(conn, cur, pid) #participants mit items
    unbound_items = select_itemlist(conn, cur, pid, "unbound")

    if request.method == "POST":
        changed_title = request.form["titel"]
        update_party(conn, cur, pid, changed_title, "title")
        print("Submit funktioniert")
        
    return render_template("bearbeiten.html", party=party, items = items, participants=participants, guests = guests, unbound_items=unbound_items)

@app.route('/friends', methods= ["GET", "POST"])
def friends():
    user = session["user"]
    
    friend_requests_to_me = check_for_friend_requests(conn, cur, user, "foreign_requests")
    my_friends = select_friends(conn, cur, user)
    len_friend_requests_to_me = len(friend_requests_to_me)

    if request.method == "POST":
        if "Acceptinvitation" in request.form:
            friend_request(conn, cur, user, request.form["Acceptinvitation"],"accept")
            flash("Freund hinzugefügt")
        elif "Declineinvitation" in request.form:
            friend_request(conn, cur, user, request.form["Declineinvitation"],"deny")
            flash("Freundschaftsanfrage abgelehnt")
        elif "delete_friend" in request.form:
            friend_request(conn, cur, user, request.form["delete_friend"],"delete")
            flash("Freundschaft gelöscht")
        
        return redirect(url_for("friends"))
        
        friends = select_friends(conn, cur, user)
       
    return render_template('friends.html', friend_requests_to_me=friend_requests_to_me, my_friends=my_friends, len_friend_requests_to_me=len_friend_requests_to_me)

@app.route('/addfriend', methods = ["GET", "POST"])
def addfriend():
    form = AddFriend()
    session._get_current_object.__name__
    user = session["user"]

    if form.validate_on_submit():
        session._get_current_object.__name__        
        session["user_search"] = form.user.data
        
        suchergebnisse = search_user(conn, cur, session["user_search"], user)
        print (suchergebnisse)
        return render_template ('addfriend.html', form=form, suchergebnisse=suchergebnisse)
    
    if "Hinzufügen" in request.form:
        friend_request(conn, cur, user, request.form["Hinzufügen"], "request")
        flash('Freund hinzugefügt')
        print("flashing")
        return redirect(url_for('addfriend'))
        
    return render_template('addfriend.html', form=form)

@app.route('/invitations', methods=['POST', 'GET'])
def invitations():
    session._get_current_object.__name__
    user = session["user"]
    
    invites = select_open_party_invites(conn, cur, user)
    print(invites)
    if request.method == "POST":
        
        if "Accept" in request.form:
            change_participants(conn, cur, request.form["Accept"], user, "accept")
            pid = request.form["Accept"]
            return redirect(url_for('accept', pid=pid))
        elif "Decline" in request.form:
            change_participants(conn, cur, request.form["Decline"], user, "delete")
            pid = request.form["Decline"]
            return redirect(url_for("dashboard"))

        

    return render_template('invitations.html', invites = invites)

@app.route("/accept/<pid>", methods=['POST', 'GET'])
def accept(pid):
    session._get_current_object.__name__
    user = session["user"]

    change_participants(conn, cur, pid, user, "accept")
    
    party = view_party(conn, cur, pid) #Tupel mit den Party Attributen
    items = select_itemlist(conn, cur, pid, "unbound") #Liste aller Items als Tupel bestehend aus item und brought_by
    
    if request.method == "POST":
        flash('Itemliste aktualisiert')
        print("flashing")
        for item in request.form.getlist("checkbox"):
             change_itemlist(conn, cur, pid, item, "assign_to", user)
             print(item)
        return redirect(url_for('dashboard'))
             
    return render_template('anzeigen.html', items = items, party = party)

@app.route("/logout/", methods=['POST'])
def Logout():
    session._get_current_object.__name__    
    forward_message = "Moving Forward..."
    if request.method == 'POST':
        session['logged_in']=False
        session["address"] = None
        session ['user'] = None
        print("Logged out")
        return render_template('start.html')
        
        
    return render_template('dashboard.html', forward_message=forward_message) 

if __name__ == '__main__':
    app.run()
    app.run(debug=True)