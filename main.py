from flask import Flask,render_template,session, request, flash,url_for,redirect
import sqlite3
from passlib.hash import pbkdf2_sha256
from frameworks import User,Account
from tools import get_user_info,sql_read,sql_write
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)


@app.route('/')
def home():
    if session.get("email"):
        user = User(*get_user_info(session.get("email")))
        accounts = sql_read(("SELECT * from Account WHERE Account.Email = ?",(user.email,)))
        accounts = list(map(lambda parameters: Account(*paramenters),accounts))
        return render_template("cash.html",accounts = accounts)
    else:
        return render_template('login.html')

@app.route('/process_login',methods = ["POST"])
def process_login():
    data = request.form
    db = sqlite3.connect("database.db")
    user_data = get_user_info(data["email"])
    if not user_data:
        flash("⚠ Account does not exist")
        db.close()
        return redirect(url_for("login"))
    user = User(*user_data)
    
    if pbkdf2_sha256.verify(data["password"],user.password):
        session["email"] = user.email
        return redirect(url_for("home"))
        
    
@app.route('/register')
def register():
    if session.get('email'):
        return redirect(url_for("home"))
    return render_template('register.html')
    
@app.route('/process_register',methods = ['POST'])
def process_register():
    data = request.form
    if get_user_info(data["email"]):
        flash("⚠ Account already exists",category = "danger")
        return redirect(url_for("register"))
    else:
        sql_write(("INSERT INTO User VALUES (?,?,?)",(data["email"],data["name"],pbkdf2_sha256.hash(data["password"]))))
        flash("Account Successfully created",category = "success")
        return redirect(url_for("home"))

@app.route('/transaction')
def transactions():
    return render_template('add_transaction.html')

@app.errorhandler(404)
def notfound(e):
    return render_template('404.html'),404
app.run(port = 5000)