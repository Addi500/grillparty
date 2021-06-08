import datetime
from flask import Flask, render_template
from flask.globals import session
from flask.helpers import flash
from flask_wtf import FlaskForm, form
from wtforms import fields 
from wtforms.fields.core import DateField, Field, SelectField, StringField
from wtforms.validators import Email, InputRequired, data_required, email, equal_to, length
from wtforms.fields.simple import PasswordField, SubmitField, TextAreaField
from wtforms.fields.html5 import DateField, TimeField
from backend import *

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'secretKeyForCookieGeneration'

db_name = "dbrun1.db"
initial_db(db_name)
conn, cur = establish_connection(db_name)

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

class NewEvent(FlaskForm):
    title = StringField(label="Titel ")
    date = DateField(label="Datum", format='%d.%m.%y')
    time = TimeField(label="Uhrzeit")
    itemlist = TextAreaField(label="ArtikellisteTobedone")
    address = TextAreaField(label="Ort")
    Teilnehmer = TextAreaField (label="Teilnehmer tbd")
    submit = SubmitField("Erstellen")
    


#app.route gehören zur View?
@app.route('/')
def index():
    return render_template('start.html')

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
            return render_template("dashboard.html")
        else:
            print("wrong pw")
            #falsches Passwort
            pass

    return render_template("login.html", form=form)

@app.route("/newevent", methods= ["GET", "POST"])
def newevent():
    form = NewEvent()
    if form.validate_on_submit():
        session._get_current_object.__name__
        session["title"] = form.title.data
        session["date"] = form.date.data
        session["time"] = form.time.data
        session["itemlist"] = form.itemlist.data
        session["address"] = form.address.data
        session["Teilnehmer"] = form.Teilnehmer.data
        print("if ")
        return render_template("registrate_success.html")
    return render_template("newevent.html", form=form)

@app.route("/dashboard")
def dashbard():
    return render_template("dashboard.html")


if __name__ == '__main__':
    app.run()
    #app.run(debug=True)