from flask import Flask,render_template,session, request, flash,url_for,redirect
import sqlite3
from passlib.hash import pbkdf2_sha256
from frameworks2 import User,Account,SpendingAccount
from tools import get_user_info,sql_read,sql_write
import os
import functools

app = Flask(__name__)
app.secret_key = os.urandom(24)

def login_required(route):
    @functools.wraps(route)
    def route_wrapper(*args,**kwargs):
        if session.get("email") is None:
            return redirect(url_for("home"))
        return route(*args,**kwargs)
    return route_wrapper

@app.route('/')
def home():
    if session.get("email"):
        user = User(*get_user_info(session.get("email")))
        accounts = sql_read(("SELECT * from Account WHERE Account.Email = ?",(user.email,)))
        accounts = list(map(lambda parameters: Account(*parameters),accounts))
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

@app.route('/add_account')
@login_required
def add_account():
    SpendingAccounts = [SpendingAccount(*AccountData) for AccountData in sql_read(("SELECT * FROM SpendingAccount WHERE SpendingAccount.Approval  = 1;",))]
    return render_template("add_account.html",SpendingAccounts = SpendingAccounts)

@app.route("/process_account",methods = ["POST"])
@login_required
def process_account():
    data = request.form
    accounts = sql_read(("SELECT * from Account WHERE Account.Email = ?",(user.email,)))
    accounts = list(map(lambda parameters: Account(*parameters),accounts))
    if any([account.AccountName == data["account"] and account.Amount == float(data["amount"]) for account in accounts]):
        flash("Account already exists",category = "danger")
        return redirect(url_for('home'))
    sql_write(("INSERT INTO Account(Email,AccountName,Amount) VALUES (?,?,?,?);",(session.get("email"),data["account"],float(data["amount"]))))
    flash("Spending option Added",category="success")
    return redirect(url_for('home'))

@app.route("/process_SpendingAccount" , methods = ["POST"])
@login_required
def process_SpendingAccount():
    #INSERT INTO SpendingAccount (AccountName, Approval, RequestEmail) VALUES ('OCBCS', 0, 'test');
    account_name = request.form["account_name"]
    SpendingAccounts = [SpendingAccount(*AccountData) for AccountData in sql_read(("SELECT * FROM SpendingAccount WHERE SpendingAccount.Approval  = 1;",))]
    if any([account.AccountName == account_name for account in SpendingAccounts]):
        flash("Spending Option already exists",category="danger")
        
    sql_write()
app.run(port = 5001)