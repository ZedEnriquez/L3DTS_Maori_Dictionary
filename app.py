# Zed's Maori Dictionary :)

# Imports
from flask import Flask, render_template, request, session, redirect
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime

# Necessary Code
app = Flask(__name__)
app.secret_key = "twentyone"
DATABASE = 'M_dictionary.db'

# Bcrypt is used to hash the user's passwords.
bcrypt = Bcrypt(app)


# Connecting the database
def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        connection.execute('pragma foreign_keys=ON')
        return connection
    except Error as e:
        print(e)
    return None


# Collecting Category Names
def categories():

    # The task is to obtain the "id" and "category_name" rows (including its information)
    # from the "categories" table.
    query = "SELECT id, category_name FROM categories ORDER BY category_name ASC"

    # The program then retrieves the data/ performs the task
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query)

    # The data that has been obtained has now been put in a list and is called "category_list"
    category_list = cur.fetchall()
    con.close()
    return category_list


# Fetching the contents for the specified category
def dictionary_data():
    con = create_connection(DATABASE)

    # The task: To obtain all the contents within the "dictionary" table.
    query = "SELECT * FROM dictionary ORDER BY Maori ASC "

    # The task is performed and the collated information is now referred to "contents"
    cur = con.cursor()
    cur.execute(query,)
    contents = cur.fetchall()
    con.close()
    return contents


# Checking the login state
def is_logged_in():
    if session.get("email") is None:
        print("not logged in")
        return False
    else:
        print("logged in")
        return True


# Checking if the user is a teacher
def is_teacher():

    # 1 = True, 0 = False
    if session.get("teacher") == 0:
        print("A teacher isn't logged in")
        return False
    else:
        print("A Teacher is logged in")
        return True


# Obtaining the user
def user_details():
    con = create_connection(DATABASE)

    # The task: To obtain the fname, lname, and id rows from the "users" table
    query = "SELECT fname, lname, id FROM users"

    # The task is performed and the collated information is now referred to "user_obtained"
    cur = con.cursor()
    cur.execute(query,)
    user_obtained = cur.fetchall()
    con.close()
    return user_obtained


# Homepage
@app.route('/')
def render_homepage():
    print(session)

    # Here the "home.html" template is rendered and a list of functions are called.
    return render_template("home.html", logged_in=is_logged_in(), contents=dictionary_data(),
                           categories_obtained=categories(), teacher_perm=is_teacher(), user_obtained=user_details())


# User Signup
@app.route('/signup', methods=['GET', 'POST'])
def render_signup_page():
    if is_logged_in():
        return redirect('/')
    if request.method == 'POST':     # Post is the method used after submitting your details on the form.
        print(request.form)
        fname = request.form.get('fname').strip().title()     # .get: Websites gets the information.
        lname = request.form.get('lname').strip().title()     # .strip().title() Sanitizes the details.
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        password2 = request.form.get('password2')
        teacher = request.form.get('teacher')

        # User gets sent back to the signup form
        # because they included more than just characters
        # in their first and last names.

        if not fname.isalpha():
            return redirect('/signup?error=No+symbols+pls')

        if not lname.isalpha():
            return redirect('/signup?error=No+symbols+pls')

        if password != password2:     # Notifies the user that there is has been an input problem.
            return redirect('/signup?error=Passwords+dont+match')

        if len(password) < 8:     # Requires the user to have a more lengthy password.
            return redirect('/signup?error=Passwords+be+8+characters+or+more')

        # password gets jumbled preventing it from being able to be hacked and used.
        hashed_password = bcrypt.generate_password_hash(password)

        con = create_connection(DATABASE)

        # inserts the details (submitted through the signup form) into the "users" table.
        query = "INSERT INTO users(id, fname, lname, email, password, teacher) VALUES(NULL,?,?,?,?,?)"
        cur = con.cursor()

        # The program will try to insert the new details in the "users" table.
        # However, if an existing email is trying to be reused then the user
        # will get sent back to the signup page.
        try:
            cur.execute(query, (fname, lname, email, hashed_password, teacher))
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+used')
        con.commit()
        con.close()

        return redirect("/login")

    error = request.args.get('error')
    if error is None:
        error = ""
    return render_template("signup.html", error=error, categories_obtained=categories())


# User Login
@app.route('/login', methods=["GET", "POST"])
def render_login_page():
    if is_logged_in():
        return redirect('/')
    if request.method == 'POST':
        print(request.form)
        email = request.form['email'].strip().lower()
        password = request.form['password'].strip()
        query = "SELECT id, fname, password, teacher FROM users WHERE email = ?"
        con = create_connection(DATABASE)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()
        try:
            userid = user_data[0][0]
            firstname = user_data[0][1]
            db_password = user_data[0][2]
            teacher = user_data[0][3]

        # If there has been an input error the program will redirect the user back to the login page.
        except IndexError:
            return redirect("/login?error=Email+invalid+or+password+incorrect")
        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + "?error=Email+invalid+or+password+incorrect")

        session['email'] = email
        session['userid'] = userid
        session['firstname'] = firstname
        session['teacher'] = teacher
        print(session)
        return redirect('/')
    return render_template("login.html", logged_in=is_logged_in(),
                           categories_obtained=categories(), teacher_perm=is_teacher())


# User Logout
@app.route('/logout')
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect('/?message=See+you+next+time!')


# User can add a category
@app.route('/add_category', methods=["GET", "POST"])
def render_add_category_page():

    # The user has to be a teacher in order to add a category.
    if is_teacher() == 0:
        return redirect('/')

    if request.method == 'POST':
        print(request.form)
        cat_name = request.form['category_name'].strip().title()

        if not cat_name.isalpha():     # The name of the category must be in characters only.
            return redirect('/?error=No+symbols+pls')

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
    if error is None:
        error = ""
    return render_template("add_category.html", error=error, logged_in=is_logged_in(),
                           categories_obtained=categories(), teacher_perm=is_teacher())


# Displaying the Category page  (includes the add a new word ability)
@app.route('/category/<cat_id>', methods=["GET", "POST"])
def render_category_page(cat_id):

    # The Add a new word ability at the bottom of the page
    if request.method == 'POST':     # Post is the method used after submitting your details.
        print(request.form)
        new_maori = request.form.get('maori').strip().title()     # .get: Websites gets the information.
        new_english = request.form.get('english').strip().title()     # .strip().title() Sanitizes the details.
        new_definition = request.form.get('definition').strip()
        new_level = request.form.get('level').strip()
        new_image = 'no_image.png'
        new_date = datetime.now()

        # Inserts the word into the category
        con = create_connection(DATABASE)
        query = "INSERT INTO dictionary (id, Maori, English, cat_id, " \
                "Definition, Level, Image, date) VALUES(NULL,?,?,?,?,?,?,?)"
        cur = con.cursor()
        try:
            cur.execute(query, (new_maori, new_english, cat_id, new_definition, new_level, new_image, new_date,))
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+used')
        con.commit()
        con.close()

    return render_template('category.html', contents=dictionary_data(), categories_obtained=categories(),
                           cat_id=int(cat_id), logged_in=is_logged_in(),
                           teacher_perm=is_teacher())


# User can delete a category
@app.route('/remove_category/<cat_id>')
def render_remove_category_page(cat_id):
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')
    if not is_teacher():
        return redirect('/?error=A+teacher+is+not+logged+in')
    return render_template('remove_category.html', categories_obtained=categories(), cat_id=int(cat_id),
                           logged_in=is_logged_in(), teacher_perm=is_teacher(), contents=dictionary_data())


# Confirmation when you delete a category
@app.route('/confirm_remove_category/<cat_id>')
def render_confirm_remove_category_page(cat_id):
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')

    if not is_teacher():
        return redirect('/?error=Teacher+is+not+logged+in')

    con = create_connection(DATABASE)
    query = "DELETE FROM categories WHERE id = ?"
    cur = con.cursor()
    cur.execute(query, (cat_id,))
    con.commit()
    con.close()
    return redirect('/?The+category+has+been+removed')


# Displaying the specific word (Includes the edit a word ability)
@app.route('/word/<word_id>', methods=["GET", "POST"])
def render_word_page(word_id):
    if request.method == 'POST':

        if not is_logged_in():
            return redirect('/?error=Not+logged+in')

        if not is_teacher():
            return redirect('/?error=Teacher+is+not+logged+in')

        print(request.form)
        edit_maori = request.form.get('edit_maori').strip().title()
        edit_english = request.form.get('edit_english').strip().title()
        edit_definition = request.form.get('edit_definition')
        edit_level = request.form.get('edit_level').strip()
        edit_user = session.get('userid')

        # Replacing the contents of the word with its new ones.
        con = create_connection(DATABASE)
        cur = con.cursor()

        query = "UPDATE dictionary SET Maori=?, English=?, Definition=?, Level=?, User_id=? WHERE id=?"

        cur.execute(query, (edit_maori, edit_english, edit_definition, edit_level, edit_user, word_id))
        con.commit()
        con.close()
        return redirect('/word/'+str(word_id))

    return render_template('word.html', contents=dictionary_data(), categories_obtained=categories(),
                           logged_in=is_logged_in(), teacher_perm=is_teacher(), word_id=int(word_id),
                           user_obtained=user_details())


# User can delete a word
@app.route('/remove_word/<word_id>')
def render_remove_word_page(word_id):
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')
    if not is_teacher():
        return redirect('/?error=A+teacher+is+not+logged+in')
    return render_template('remove_word.html', categories_obtained=categories(), logged_in=is_logged_in(),
                           teacher_perm=is_teacher(), contents=dictionary_data(), word_id=int(word_id))


# Conformation when deleting a word
@app.route('/confirm_remove_word/<word_id>')
def render_confirm_remove_word_page(word_id):
    if not is_logged_in():
        return redirect('/?error=Not+logged+in')
    if not is_teacher():
        return redirect('/?error=A+teacher+is+not+logged+in')

    con = create_connection(DATABASE)
    query = "DELETE FROM dictionary WHERE id = ?"
    cur = con.cursor()
    cur.execute(query, (word_id,))
    con.commit()
    con.close()
    return redirect('/?The+word+has+been+removed')


# Running the app
if __name__ == '__main__':
    app.run()
