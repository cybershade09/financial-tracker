import sqlite3
import requests
def get_user_info(email,database_name = "database.db"):
    db = sqlite3.connect(database_name)
    c = db.execute("SELECT * FROM User WHERE User.email = ?",(email,))
    data = c.fetchone()
    db.close()
    return data
    
def sql_read(query,mode = 1,database_name = "database.db"):
    db = sqlite3.connect(database_name)
    c  = db.execute(*query)
    data = [sqlite3.Cursor.fetchone,sqlite3.Cursor.fetchall][mode](c)
    db.close()
    return data

def sql_write(query,mode = 1,database_name = "database.db"):
    db = sqlite3.connect(database_name)
    c  = db.execute(*query)
    db.commit()
    db.close()
