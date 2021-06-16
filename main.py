
from datetime import date
from re import UNICODE
import sqlite3
from sqlite3.dbapi2 import Time
from flask import Flask, render_template, request
from flask.globals import session
from flask_wtf import FlaskForm
from wtforms.fields import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.fields.html5 import DateField, SearchField
from wtforms.validators import Email, InputRequired, data_required, email, equal_to, length
from backend import *
from wtforms_components import TimeField
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user


app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'secretKeyForCookieGeneration'

db_name = "dbrun1.db"
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
    title = StringField(label="Titel ")
    date = DateField(label="Datum", default = date.today())
    time = TimeField(label="Uhrzeit")
    address = TextAreaField(label="Ort")
    Teilnehmer = SearchField (label="Teilnehmer tbd")
    submit = SubmitField("Erstellen")


class Friends(FlaskForm):
    user = SearchField()
    submit = SubmitField("Suchen")
 

@app.route('/')
def index():
    return render_template('start.html')

@app.route('/help')
def help():
    return render_template('help.html')

@app.route("/registrate", methods=["GET","POST"])
def registrate():
    form = Registrate()
    if form.validate_on_submit():
        session._get_current_object.__name__
        session["User"] = form.User.data
        session["address"] = form.mailaddress.data
        session["password"] = form.password.data
        print("if ")
        insert_into_users(conn, cur, session["address"], session["User"], session["password"])
        return render_template("registrate_success.html")
    return render_template("registrate.html", form=form)

    #Button zu Anmeldung in die html registrate-success einbauen

@app.route("/login", methods=["GET","POST"])
def login():
    form = Login()
    
            
    if form.validate_on_submit():
        session._get_current_object.__name__
        
        session["address"] = form.mailaddress.data
        session["password"] = form.password.data
        
        print("if ")
        if check_login(conn, cur, session["address"], session["password"]):
            print("correct pw")
            
            session['logged_in']=True
            #current_user = session["address"] 
            return render_template("dashboard.html")
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
    
    ###tbd: USER NAME ÜBERGEBEN!!!!
    user = "test2@123.com"


    if form.validate_on_submit():

        session._get_current_object.__name__
        session["title"] = form.title.data
        session["date"] = form.date.data
        session["time"] = str(form.time.data)
        session["address"] = form.address.data
        session["Teilnehmer"] = form.Teilnehmer.data
        session["itemlist"] = request.form.getlist('field[]')
        print("itemliste: ", session["itemlist"])
        
        print("if ")
        id = insert_into_parties(conn, cur, session["title"], session["date"], session["time"], session["address"],user)
        for item in session["itemlist"]:
            insert_into_itemlist(conn, cur, id, item) #change to list above
        for participant in session["Teilnehmer"]:
            insert_into_participants(conn, cur, id, participant) #change to list above
        return render_template("registrate_success.html")
    return render_template("newevent.html", form=form)

@app.route("/dashboard")
def dashbard():
    return render_template("dashboard.html")

@app.route('/friends', methods= ["GET", "POST"])
def friends():
    
    form = Friends()
    user = session["address"]
    if form.validate_on_submit():

        session._get_current_object.__name__
        
        session["user"] = form.user.data

        suchergebnisse = search(conn, cur, "users", session["user"])
        print (suchergebnisse)

    return render_template('friends.html', form=form, friends=friends)
    
#übergibt gesuchten User. Funktion für Buttons fehlt noch
@app.route("/acceptinv/", methods=['POST'])
def AcceptFriends():
    session._get_current_object.__name__
    
    if request.method == 'POST':
        if request.form['Acceptinvitation'] == '0':
            print("1")
        elif request.form['Acceptinvitation'] == '2':
            print("2")

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

@app.route('/invitations')
def invitations():
    user = session["address"]
    #user = "test@132.com"
    
    invites = select_open_party_invites(conn, cur, user)
    print(invites)
    
    #check_for_friend_requests(conn, cur, user)
    return render_template('invitations.html', invites = invites)

@app.route("/accept/", methods=['POST'])
def Accept():
    session._get_current_object.__name__
    
    if request.method == 'POST':
        if request.form['Accept'] == '0':
            print("1")
        elif request.form['Accept'] == '2':
            print("2")

    # Abgleich mit db nicht über if sondern anhand Buttonvalue akzeptieren (von 0 auf 1 setzen)
    #Moving forward code
    
    forward_message = "Moving Forward..."

    return render_template('invitations.html', forward_message=forward_message);    
    
#keine Klasse bisher angelegt, benötigt Übergabe der Einladungen aus der
#Datenbank, Buttons noch ohne Funktion, Einladungsart (Freunde / Veranstaltung)
# Einladung von: User, bei Veranstaltung komplette Ausgabe der Einladnung, neue form
# für Auswahl der Mitbringsel


if __name__ == '__main__':
    app.run()
    app.run(debug=True)