from flask import Flask, render_template, request, session, redirect
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime

import smtplib, ssl
from smtplib import SMTPAuthenticationError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
bcrypt = Bcrypt(app)
DATABASE = 'maori_dictionary.db'


def create_connection(db_file):     # Connects the desired database file
    try:
        connection = sqlite3.connect(db_file)
        connection.execute('pragma foreign_keys=ON')
        return connection
    except Error as e:
        print(e)
    return None

@app.route('/')
def render_homepage():
    return render_template("home.html")

@app.route('/login')
def render_login_page():
    return render_template("login.html")

def is_logged_in():
    if session.get("email") is None:
        print("not logged in")
        return False
    else:
        print("logged in")
        return True


@app.route('/signup', methods=['GET', 'POST'])
def render_signup_page():
    if is_logged_in():
        return redirect('/')

    if request.method == 'POST':     # Post is the method used after submitting your details.
        print(request.form)
        fname = request.form.get('fname').strip().title()     # .get: Websites gets the information.
        lname = request.form.get('lname').strip().title()     # .strip().title() Sanitizes the details.
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        password2 = request.form.get('password2')

        if password != password2:     # Notifies the user that there is an input problem.
            return redirect('/signup?error=Passwords+dont+match')

        if len(password) < 8:     # Requires the user to have a more secure password.
            return redirect('/signup?error=Passwords+be+8+characters+or+more')

        hashed_password = bcrypt.generate_password_hash(password)     # password gets jumbled preventing it from
                                                                      # being able to be hacked and used.

        con = create_connection(DATABASE)     # creates the connection with the desired database file.

        query = "INSERT INTO users(id, fname, lname, email, password) VALUES(NULL,?,?,?,?)"     # inserts into "users."

        cur = con.cursor()
        try:
            cur.execute(query, (fname, lname, email, hashed_password))
        except sqlite3.IntegrityError:
            return redirect('/signup?error=email+is+already+used')

        con.commit()
        con.close()
        return redirect("/login")
    error = request.args.get('error')

    if error == None:
        error = ""

    return render_template("signup.html", error=error)

# This line allows the app to run.
if __name__ == '__main__':
    app.run()