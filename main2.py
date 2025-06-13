from flask import Flask,render_template,session, request, flash,url_for
import sqlite3
from passlib.hash import pbkdf2_sha256

app = Flask(__name__)

@app.route('/')
def home():
    if session.get("email"):
        pass
    else:
        return render_template('login.html')

@app.route('process_login')
def process_login(methods = ["POST"]):
    data = request.from
    
@app.route('/register')
def register():
    if session.get('email'):
        return redirect(url_for(home))
    return render_template('register.html')
    
@app.route('process_register')
def process_register(methods = ['POST']):
    data = request.from
    db = sqlite3.connect("database.db")
    if db.execute("SELECT * FROM User WHERE User.Email = ?",(data["email"])).fetchone():
        flash("⚠ Account already exists",category = "danger")
        db.close()
        return redirect(url_for(register))
    else:
        db.execute("INSERT INTO User value (?,?,?,?)",(data["email"],data["name"],pbkdf2_sha256.hash(data["password"])))
        flash("Account Successfully created",category = "success")
        db.close()
        return redirect(url_for(home))
        
app.run(port = 5000)