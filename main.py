from flask import Flask,render_template,session, request, flash,url_for,redirect,abort
import sqlite3
from passlib.hash import pbkdf2_sha256
from frameworks import User,Account,SpendingAccount,Transaction
from tools import get_user_info,sql_read,sql_write
import os
import functools
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import json
from datetime import date,datetime,timedelta
import uuid
import requests

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("SECRET_KEY")

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
        if user.email in os.getenv('ADMIN_USERS').split(','):
            return redirect(url_for('admin'))
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
        if data["password"]!=data["cfm_password"]:
            flash("⚠ Passwords don't match",category = "danger")
            return redirect(url_for("register"))
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
    sql_write(("INSERT INTO AccountIDMap(Email,AccountName,NameOnCard) VALUES (?,?,?);",(session.get("email"),data["account"],data["name_on_card"])))
    flash("Spending option Added",category="success")
    return redirect(url_for('home'))

@app.route("/process_SpendingAccount" , methods = ["POST"])
@login_required
def process_SpendingAccount():
    account_name = request.form["account_name"]
    SpendingAccounts = [SpendingAccount(*AccountData) for AccountData in sql_read(("SELECT * FROM SpendingAccount WHERE SpendingAccount.Approval  = 1;",))]
    if any([account.AccountName == account_name for account in SpendingAccounts]):
        flash("Spending Option already exists",category="danger")
        return redirect(url_for('home'))
    SpendingAccounts = [SpendingAccount(*AccountData) for AccountData in sql_read(("SELECT * FROM SpendingAccount WHERE SpendingAccount.Approval  = 0;",))]
    if not any([account.AccountName == account_name for account in SpendingAccounts]):    
        sql_write(("INSERT INTO SpendingAccount(AccountName,Approval,RequestEmail) VALUES (?,?,?)",(account_name,False,session.get("email"))))
    flash("Request sent",category="success")
    return redirect(url_for('home'))



@app.route("/history/<AccountDetails>",methods = ["GET","POST"])
@login_required
def history(AccountDetails):
    cipher = Fernet(os.getenv("FERENET_KEY").encode())
    account = Account.from_dict(json.loads(cipher.decrypt(AccountDetails.encode()).decode()))
    if account.Email != session.get("email"):
        return abort(403)
    
    sql = """SELECT AccountIDMap.AccountID FROM AccountIDMap WHERE
    AccountIDMap.Email = ? AND 
    AccountIDMap.AccountName = ? AND 
    AccountIDMap.NameOnCard = ?;"""
    AccountID = sql_read((sql,(account.Email,account.AccountName,account.NameOnCard)),0)[0]
    time_frame = ['0-0-0',datetime.today().strftime("%Y-%m-%d"),(datetime.today()-timedelta(days = 6)).strftime("%Y-%m-%d"),(datetime.today()-timedelta(days = 30)).strftime("%Y-%m-%d")]
    if request.method == "GET" or request.form["filter"] ==  "All Time":
        selected = 0
    elif  request.form["filter"] == "1 day":
        selected = 1
    elif request.form["filter"] == "1 week":
        selected = 2
    elif request.form["filter"] == "1 month":
        selected = 3
    
    transactions = [Transaction(*transaction) for transaction in sql_read(("SELECT Transactions.*,TransactionType.IsExpense FROM Transactions,TransactionType WHERE TransactionType.TransactionID = Transactions.TransactionID AND Transactions.AccountID = ? AND Transactions.Date >= ? ORDER BY Transactions.Date DESC;",(AccountID,time_frame[selected])))]
    return render_template("transaction_history.html",account = account, transactions = transactions,AccountDetails = AccountDetails,select = selected)

@app.route("/add_transaction/<AccountDetails>")
@login_required
def add_transaction(AccountDetails):
    cipher = Fernet(os.getenv("FERENET_KEY").encode())
    account = Account.from_dict(json.loads(cipher.decrypt(AccountDetails.encode()).decode()))
    if account.Email != session.get("email"):
        return abort(403)
    return render_template("add_transaction.html",current_date =date.today().isoformat() )

@app.route("/process_transaction",methods = ["POST"])
@login_required
def process_transaction():
    AccountDetails = request.referrer.split('/')[-1]
    cipher = Fernet(os.getenv("FERENET_KEY").encode())
    account = Account.from_dict(json.loads(cipher.decrypt(AccountDetails.encode()).decode()))
    if account.Email != session.get("email"):
        return abort(403)
    sql = """SELECT AccountIDMap.AccountID FROM AccountIDMap WHERE
    AccountIDMap.Email = ? AND 
    AccountIDMap.AccountName = ? AND 
    AccountIDMap.NameOnCard = ?;"""
    AccountID = sql_read((sql,(account.Email,account.AccountName,account.NameOnCard)),0)[0]
    data = request.form
    if data["type"] == "income":
        account.Amount += float(data["amount"])
        sql_write(("UPDATE Account SET Amount = ? WHERE Account.Email = ? AND Account.AccountName = ? AND Account.NameOnCard = ? ;",(account.Amount,account.Email,account.AccountName,account.NameOnCard)))
        ids = sql_read(("SELECT Transactions.TransactionID FROM Transactions",))
        TransactionID = uuid.uuid4().hex
        while TransactionID in ids:
            TransactionID = uuid.uuid4().hex
        
        transaction = Transaction(TransactionID,AccountID,data["date"],float(data["amount"]),data["description"],data["category"],False)
        sql_write(("INSERT INTO Transactions(TransactionID,AccountID,Date,Amount,Description,Category) VALUES (?,?,?,?,?,?);",(transaction.TransactionID,transaction.AccountID,transaction.Date,transaction.Amount,transaction.Description,transaction.Category)))
        sql_write(("INSERT INTO TransactionType(TransactionID,IsExpense) VALUES (?,?);",(transaction.TransactionID,transaction.IsExpense)))
        return redirect(url_for('history',AccountDetails = cipher.encrypt(json.dumps(account.to_dict()).encode()).decode()))
    else:
        if account.Amount -float(data["amount"])<0:
            flash("Insufficient funds",category = "danger")
            
            return redirect(url_for('history',AccountDetails=AccountDetails))
        else:
            account.Amount -= float(data["amount"])
            sql_write(("UPDATE Account SET Amount = ? WHERE Account.Email = ? AND Account.AccountName = ? AND Account.NameOnCard = ? ;",(account.Amount,account.Email,account.AccountName,account.NameOnCard)))
            ids = sql_read(("SELECT Transactions.TransactionID FROM Transactions",))
            TransactionID = uuid.uuid4().hex
            while TransactionID in ids:
                TransactionID = uuid.uuid4().hex
            
            transaction = Transaction(TransactionID,AccountID,data["date"],float(data["amount"]),data["description"],data["category"],True)
            sql_write(("INSERT INTO Transactions(TransactionID,AccountID,Date,Amount,Description,Category) VALUES (?,?,?,?,?,?);",(transaction.TransactionID,transaction.AccountID,transaction.Date,transaction.Amount,transaction.Description,transaction.Category)))
            sql_write(("INSERT INTO TransactionType(TransactionID,IsExpense) VALUES (?,?);",(transaction.TransactionID,transaction.IsExpense)))
            flash("Transaction logged",category="success")
            return redirect(url_for('history',AccountDetails = cipher.encrypt(json.dumps(account.to_dict()).encode()).decode()))

@app.route("/transaction_details/<transactionID>")
@login_required
def transaction_details(transactionID):
    transaction = sql_read(("SELECT Transactions.*,TransactionType.IsExpense FROM Transactions,TransactionType WHERE TransactionType.TransactionID = Transactions.TransactionID AND Transactions.TransactionID = ?;",(transactionID,)),0)
    if not transaction:
        return redirect(url_for('home'))
    
    transaction = Transaction(*transaction)
    if sql_read(("SELECT AccountIDMap.Email FROM AccountIDMap WHERE AccountIDMAP.AccountID = ?;",(transaction.AccountID,)),0)[0] != session.get("email"):
        return abort(403)
    
    return render_template("view_details.html",transaction = transaction)

@app.route("/delete_transaction/<transactionID>",methods=["POST"])
@login_required
def delete_transaction(transactionID):
    transaction = sql_read(("SELECT Transactions.*,TransactionType.IsExpense FROM Transactions,TransactionType WHERE TransactionType.TransactionID = Transactions.TransactionID AND Transactions.TransactionID = ?;",(transactionID,)),0)
    if not transaction:
        return redirect(url_for('home'))
    
    transaction = Transaction(*transaction)
    if sql_read(("SELECT AccountIDMap.Email FROM AccountIDMap WHERE AccountIDMAP.AccountID = ?;",(transaction.AccountID,)),0)[0] != session.get("email"):
        return abort(403)
    
    if not transaction.IsExpense:
        sql = """SELECT Transactions.Date, Transactions.Amount, TransactionType.IsExpense 
    FROM Transactions,TransactionType
    WHERE TransactionType.TransactionID = Transactions.TransactionID AND Transactions.AccountID = ?
    ORDER BY Transactions.Date ASC;"""
        data = sql_read((sql,(transaction.AccountID,)))
        history_data = {}
        range_list = []
        for record in data:
            if record[0] not in range_list:
                range_list.append(record[0])
            history_data[record[0]] = history_data.get(record[0],0)+(record[1]*[1,-1][record[2]])
        amount = sql_read(("SELECT Account.Amount FROM AccountIDMap,Account WHERE AccountIDMap.AccountName = Account.AccountName AND AccountIDMAP.Email = Account.Email AND AccountIDMap.NameOnCard = Account.NameOnCard AND AccountIDMap.AccountID = ?;",(transaction.AccountID,)),0)[0]
        for key in range_list[::-1]:
                value = history_data.get(key,0)
                history_data[key] = amount
                amount -= value

        for key,value in history_data.items():
            if  key>=transaction.Date:
                history_data[key] = value - transaction.Amount

        if any(value<0 for value in list(history_data.values())):
            flash('Invalid option',category="danger")
            return redirect(request.referrer)
    sql_write(("DELETE FROM Transactions WHERE Transactions.AccountID = ?;",(transaction.TransactionID,)))
    sql_write((" DELETE FROM TransactionType WHERE TransactionType.TransactionID = ?;",(transaction.TransactionID,)))
    amount = sql_read(("SELECT Account.Amount FROM AccountIDMap,Account WHERE AccountIDMap.AccountName = Account.AccountName AND AccountIDMAP.Email = Account.Email AND AccountIDMap.NameOnCard = Account.NameOnCard AND AccountIDMap.AccountID = ?;",(transaction.AccountID,)),0)[0]
    info = sql_read(("SELECT AccountIDMap.Email,AccountIDMap.AccountName,AccountIDMap.NameOnCard FROM AccountIDMAP WHERE AccountIDMAP.AccountID = ?;",(transaction.AccountID,)),0)
    sql_write(("UPDATE Account SET Amount = ? WHERE Account.Email = ? AND Account.AccountName = ? AND Account.NameOnCard = ?;",(amount- (transaction.Amount * (-1 if transaction.IsExpense else 1)),*info)))

    path = request.referrer.split('/')
    AccountDetails = path[-1]
    cipher = Fernet(os.getenv("FERENET_KEY").encode())
    account = Account.from_dict(json.loads(cipher.decrypt(AccountDetails.encode()).decode()))
    account.Amount = amount - (transaction.Amount * (-1 if transaction.IsExpense else 1))
    path[-1] = cipher.encrypt(json.dumps(account.to_dict()).encode()).decode()
    flash('Deleted Successfully',category="success")
    return redirect("/".join(path))
@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/admin')
@login_required
def admin():
    if session.get("email") not in os.getenv('ADMIN_USERS').split(','):
        return abort(403)
    data = sql_read(("SELECT SpendingAccount.AccountName, SpendingAccount.RequestEmail FROM SpendingAccount WHERE SpendingAccount.Approval = 0;",))
    return render_template("admin.html",data = data)


@app.route('/admin/process_response',methods = ["POST"])
@login_required
def process_request():
    if session.get("email") not in os.getenv('ADMIN_USERS').split(','):
        return abort(403)
    approval = request.form["ApprovalStatus"]
    if approval.startswith("approve-"):
        sql_write(("UPDATE SpendingAccount SET Approval = 1 WHERE SpendingAccount.AccountName = ?;",(approval[approval.index("-")+1:],)))  
    else:
        sql_write(("DELETE From SpendingAccount WHERE SpendingAccount.AccountName = ?;",(approval[approval.index("-")+1:],)))
    return redirect(url_for('admin'))


@app.route('/crypto_list')
def crypto_list():
    name = [(i+1,coin["name"],coin["symbol"]) for i,coin in enumerate(requests.get("https://api.coingecko.com/api/v3/coins/list").json())]
    return render_template("crypto_list.html",names=name)

@app.route('/investment')
@login_required
def investment():

    
    data = sql_read(("SELECT Investment.InvestmentHeader,Investment.Quantity FROM Investment WHERE Investment.Email = ?;",(session.get("email"),)))
    data_formatted = []
    for name,Quantity in data:
        price = requests.get("https://api.coingecko.com/api/v3/simple/price", params={'ids': name,'vs_currencies': 'sgd'}).json()

        if price and price.get(name):
            price = price[name]['sgd']
            data_formatted.append((name,f"{price:.2f}",Quantity,f"{price*Quantity:.2f}"))
        else:
            data_formatted.append((name,"-",Quantity,"-"))
    
        
    return render_template('crypto.html',data = data_formatted,value = f"{sum(float(row[-1]) for row in data_formatted if row[-1]!='-'):.2f}")

@app.route("/add_investments",methods = ["POST"])
@login_required
def add_investments():
    if request.form["cryptoName"] not in [coin["symbol"] for coin in requests.get("https://api.coingecko.com/api/v3/coins/list").json()]:
        flash("⚠ Invalid Cryptocurrency",category = "danger")
        return redirect(url_for('investment'))
    else:
        data = request.form
        past = sql_read(("SELECT Investment.Quantity FROM Investment WHERE Investment.Email = ? AND Investment.InvestmentHeader = ?;",(session.get("email"),data["cryptoName"])),0)
        if not past:
            
            sql_write(("INSERT INTO Investment(Email,InvestmentHeader,Quantity) VALUES (?,?,?);",(session.get("email"),data["cryptoName"],data["cryptoQuantity"])))
            flash("Currency Added Successfully",category = "success")
        else:
            sql_write(("UPDATE Investment SET Quantity = ? WHERE Investment.Email = ? AND Investment.InvestmentHeader = ?;",(data["cryptoQuantity"] + past[0],session.get("email"),data["cryptoName"])))
            flash("Currency updated Successfully",category = "success")
        return redirect(url_for('investment'))

@app.route('/update_investment/<crypto>/<int:option>',methods = ['POST'])
@login_required
def update_investment(crypto,option):
    if option not in [0,1,2]:
        flash("Option not available",category="danger")
    elif int(option)<2:
        data = request.form
        past = sql_read(("SELECT Investment.Quantity FROM Investment WHERE Investment.Email = ? AND Investment.InvestmentHeader = ?;",(session.get("email"),crypto)),0)
        sql_write(("UPDATE Investment SET Quantity = ? WHERE Investment.Email = ? AND Investment.InvestmentHeader = ?;",([1,-1][int(option)]*float(data["crypto_increase"]) + past[0],session.get("email"),crypto)))
        flash("Crypto updated Successfully",category = "success")
    else:
        sql_write(("DELETE FROM Investment WHERE Investment.Email = ? AND Investment.InvestmentHeader = ?;",(session.get("email"),crypto)))
        flash("Crypto deleted successfully",category="success")
    return redirect(url_for('investment'))
 
@app.route('/forex')
@login_required
def forex():
    data = sql_read(("SELECT Forex.ForeignCountry,Forex.Amount FROM Forex WHERE Forex.Email = ?;",(session.get("email"),)))
    rates = requests.get("https://api.frankfurter.app/latest?from=SGD").json()['rates']
    data = [(currency,amount,rates[currency],f"{rates[currency]*amount:.2f}") for currency,amount in data]
    return render_template('forex.html',options = list(rates.keys()),data = data,value = f"{sum(float(row[-1]) for row in data):.2f}")

@app.route('/add_forex',methods = ['POST'])
@login_required
def add_forex():
    data = request.form
    past = sql_read(("SELECT Forex.Amount FROM Forex WHERE Forex.Email = ? AND Forex.ForeignCountry = ?;",(session.get("email"),data["currency"])),0)
    if not past:
        sql_write(("INSERT INTO Forex(Email,ForeignCountry,Amount) VALUES (?,?,?);",(session.get("email"),data["currency"],float(data["currency_value"]))))
        flash("Currency Added Successfully",category = "success")
    else:
        sql_write(("UPDATE Forex SET Amount = ? WHERE Forex.Email = ? AND Forex.ForeignCountry = ?;",(float(data["currency_value"]) + past[0],session.get("email"),data["currency"])))
        flash("Currency updated Successfully",category = "success")

    return redirect(url_for('forex'))

@app.route('/update_forex/<currency>/<int:option>',methods = ['POST'])
@login_required
def update_forex(currency,option):
    if option not in [0,1,2]:
        flash("Option not available",category="danger")
    elif int(option)<2:
        past = sql_read(("SELECT Forex.Amount FROM Forex WHERE Forex.Email = ? AND Forex.ForeignCountry = ?;",(session.get("email"),currency)),0)
        sql_write(("UPDATE Forex SET Amount = ? WHERE Forex.Email = ? AND Forex.ForeignCountry = ?;",([1,-1][int(option)]*float(request.form["currency_increase"]) + past[0],session.get("email"),currency)))
        flash("Currency updated Successfully",category = "success")
    else:
        sql_write(("DELETE FROM Forex WHERE Forex.Email = ? AND Forex.ForeignCountry = ?;",(session.get("email"),currency)))
        flash("Currency deleted successfully",category="success")
    return redirect(url_for('forex'))

@app.route("/networth")
@login_required
def networth():
    # History processing
    sql = """
SELECT Transactions.Date, SUM(Transactions.Amount), TransactionType.IsExpense 
FROM Transactions,TransactionType,AccountIDMap
WHERE TransactionType.TransactionID = Transactions.TransactionID AND Transactions.AccountID = AccountIDMAP.AccountID AND AccountIDMap.Email = ?
GROUP BY Transactions.Date,TransactionType.IsExpense
ORDER BY Transactions.Date ASC;
    """
    history = sql_read((sql,(session.get("email"),)))
    if history:
        history_data = {}
        for record in history:
            history_data[record[0][:7]] = history_data.get(record[0][:7],0)+(record[1]*[1,-1][record[2]])
        first = list(history_data.items())[0][1]

        
        amount = sql_read(("SELECT SUM(Account.Amount) FROM Account WHERE Account.Email = ?;",(session.get("email"),)),0)[0]

        range_list = []
        minimum = list(history_data.items())[0][0]
        year,month = tuple(map(int,minimum.split("-")))
        
        while f"{year}-{month:02d}"<=f"{datetime.today().year}-{datetime.today().month:02d}":
            range_list.append(f"{year}-{month:02d}")
            year += (month+1)//13
            month = (month%12)+1
        
        for key in range_list[::-1]:
            value = history_data.get(key,0)
            history_data[key] = amount
            amount -= value

        year,month = tuple(map(int,minimum.split("-")))
        year -= 1 if month == 1 else 0
        month = list(range(1,13))[month-2]
        range_list = [f"{year}-{month:02d}"] + range_list
        history_data[f"{year}-{month:02d}"] = amount
        maximum_value = max(list(history_data.values()))

        amount = sql_read(("SELECT SUM(Account.Amount) FROM Account WHERE Account.Email = ?;",(session.get("email"),)),0)[0]
    else:
        amount = 0
        history_data = {}
        range_list = []
        maximum_value = ""
    
    data = sql_read(("SELECT Forex.ForeignCountry,Forex.Amount FROM Forex WHERE Forex.Email = ?;",(session.get("email"),)))
    rates = requests.get("https://api.frankfurter.app/latest?from=SGD").json()['rates']
    forex_amount = sum(rates[currency]*forex_amount for currency,forex_amount in data)

    
    
    data = sql_read(("SELECT Investment.InvestmentHeader,Investment.Quantity FROM Investment WHERE Investment.Email = ?;",(session.get("email"),)))
    data_formatted = []
    for name,Quantity in data:
        price = requests.get("https://api.coingecko.com/api/v3/simple/price", params={'ids': name,'vs_currencies': 'sgd'}).json()
        if price:
            price = price[name]['sgd']
            data_formatted.append((name,f"{price:.2f}",Quantity,f"{price*Quantity:.2f}"))
        else:
            data_formatted.append((name,"-",Quantity,"-"))
            
    crypto_amount = sum(float(row[-1]) for row in data_formatted if row[-1]!='-')

    return render_template("networth.html",history_data=history_data,range_list=range_list, maximum = maximum_value if maximum_value != 0 else 1, amount = amount + forex_amount + crypto_amount)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"),404

app.run(port = 5000)