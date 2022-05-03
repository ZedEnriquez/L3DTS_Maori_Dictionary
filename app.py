# Zed's Maori Dictionary

# Imports
from flask import Flask, render_template, request, session, redirect
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime
import smtplib, ssl
from smtplib import SMTPAuthenticationError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Necessary Code
app = Flask(__name__)
DATABASE = 'maori_dictionary.db'
app.secret_key = "twentyone"

# Bcrypt is used to hash the user's passwords.
bcrypt = Bcrypt(app)

# Collecting Category Names
def categories():
    query = "SELECT id, category_name FROM categories"
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query)
    category_list = cur.fetchall()
    con.close()
    return category_list

# Connecting the database
def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        connection.execute('pragma foreign_keys=ON')
        return connection
    except Error as e:
        print(e)
    return None

# Checking the login state
def is_logged_in():
    if session.get("email") is None:
        print("not logged in")
        return False
    else:
        print("logged in")
        return True

# Homepage
@app.route('/')
def render_homepage():
    return render_template("home.html", logged_in=is_logged_in(),
                           categories=categories()) #, categories_exist=category_list_exists)

# User Signup
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

        query = "INSERT INTO user(id, fname, lname, email, password) VALUES(NULL,?,?,?,?)"     # inserts into "user".

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

# User Login
@app.route('/login', methods=["GET", "POST"])
def render_login_page():
    if is_logged_in():
        return redirect('/')
    if request.method == 'POST':
        print(request.form)
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()
        query = """SELECT id, fname, password FROM users WHERE email = ?"""
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()
        try:
            userid = user_data[0][0]
            firstname = user_data[0][1]
            db_password = user_data[0][2]
        except IndexError:
            return redirect("/login?error=Email+invalid+or+password+incorrect")
        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + "?error=Email+invalid+or+password+incorrect")
        session['email'] = email
        session['userid'] = userid
        session['firstname'] = firstname
        print(session)
        return redirect('/')
    return render_template("login.html", logged_in=is_logged_in(), categories=categories())

# User Logout
@app.route('/logout')
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect('/?message=See+you+next+time!')

# User can add a Catergory
@app.route('/add_category', methods=["GET", "POST"])
def render_add_category_page():
    if request.method == 'POST':
        print(request.form)
        cat_name = request.form['category_name'].strip().title()
        query = "INSERT INTO categories(id, category_name) VALUES(NULL,?)"  # inserts into "categories".
        con = create_connection(DATABASE)
        cur = con.cursor()
        try:
            cur.execute(query, (cat_name, ))
        except sqlite3.ProgrammingError:
            return redirect('/?error=Incorrect+number+of+bindings+supplied')
        con.commit()
        con.close()
        return redirect("/")
    error = request.args.get('error')
    if error == None:
        error = ""
    return render_template("add_category.html", error=error, logged_in=is_logged_in(), categories=categories())

# Displaying the Category page
@app.route('/category/<Cat_id>')
def render_category_page(Cat_id):
    con = create_connection(DATABASE)

# Displaying the contents for the specified category
    query = "SELECT id, Maori, English, Cat_id, Definition, Level, Image, date FROM dictionary"
    cur = con.cursor()
    cur.execute(query)
    contents = cur.fetchall()

    query = "SELECT id, category_name FROM categories"
    cur = con.cursor()
    cur.execute(query)
    specific_category = cur.fetchall()
    con.commit()
    con.close()

    return render_template('category.html', contents = contents,
                           specific_category = specific_category, categories = categories(), Cat_id = int(Cat_id))

# Running the app
if __name__ == '__main__':
    app.run()
