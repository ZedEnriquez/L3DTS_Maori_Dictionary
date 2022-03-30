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

@app.route('/')
def render_homepage():
    return render_template("home.html")

@app.route('/login')
def render_login_page():
    return render_template("login.html")

if __name__ == '__main__':
    app.run()