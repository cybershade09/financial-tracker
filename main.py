from flask import Flask,render_template,session, request, flash,url_for,redirect,abort
import sqlite3
from passlib.hash import pbkdf2_sha256
from frameworks2 import User,Account,SpendingAccount
from tools import get_user_info,sql_read,sql_write
import os
import functools
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import json


app = Flask(__name__)
app.secret_key = os.urandom(24)
load_dotenv()

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
        cipher = Fernet(os.getenv("FERENET_KEY").encode())
        user = User(*get_user_info(session.get("email")))
        accounts = sql_read(("SELECT * from Account WHERE Account.Email = ?",(user.email,)))
        accounts = list(map(lambda parameters: Account(*parameters),accounts))
        
        total_balance = sum(account.Amount for account in accounts)
        accounts = [(account,cipher.encrypt(json.dumps(account.to_dict()).encode()).decode()) for account in accounts]
        return render_template("cash.html",accounts = accounts,total_balance=total_balance)
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
        return redirect(url_for("home"))
    user = User(*user_data)
    
    if pbkdf2_sha256.verify(data["password"],user.password):
        session["email"] = user.email
        return redirect(url_for("home"))
    else:
        flash("Wrong Username or Password",category="danger")
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
    user = User(*get_user_info(session.get("email")))
    accounts = sql_read(("SELECT * from Account WHERE Account.Email = ?",(user.email,)))
    accounts = list(map(lambda parameters: Account(*parameters),accounts))
    if any([account.AccountName == data["account"] and account.Amount == float(data["amount"]) for account in accounts]):
        flash("Account already exists",category = "danger")
        return redirect(url_for('home'))
    sql_write(("INSERT INTO Account(Email,AccountName,NameOnCard,Amount) VALUES (?,?,?,?);",(session.get("email"),data["account"],data["name_on_card"],float(data["amount"]))))
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
        
    sql_write(("INSERT INTO SpendingAccount(AccountName,Approval,RequestEmail) VALUES (?,?,?)",(account_name,False,session.get("email"))))
    flash("Request sent",category="success")
    return redirect(url_for('home'))



@app.route("/history/<AccountDetails>")
@login_required
def history(AccountDetails):
    cipher = Fernet(os.getenv("FERENET_KEY").encode())
    account = Account.from_dict(json.loads(cipher.decrypt(AccountDetails.encode()).decode()))
    if account.Email != session.get("email"):
        return abort(403)
    
    sql_read("")
    
# @app.route("/add_transaction/<AccountDetails>")
# @login_required
# def add_transaction(AccountDetails)L:
#     cipher = Fernet(os.getenv("FERENET_KEY").encode())
#     account = Account.from_dict(json.loads(cipher.decrypt(AccountDetails.encode()).decode()))
#     if account.Email != session.get("email"):
#         return abort(403)

    
@app.route('/transaction_history')
def transaction_history():
    return render_template("transaction_history.html")


@app.route('/transaction')
def add_transaction():
    return render_template("add_transaction.html")
app.run(port = 5000)