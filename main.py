from flask import Flask,render_template,session, request, flash
import sqlite3

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/register')
def register():
    if session.get('email'):
        return redirect(url_for(home))
    return render_template('register.html')  
'''    
@app.route('process_register')
def register(methods = ['POST']):
'''
app.run(port = 5000)