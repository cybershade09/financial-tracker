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

def get_forew_price():
    data = requests.get("https://api.frankfurter.app/latest?from=SGD").json()['rates']
    print(data)
    print(f"Base: {data['base']} | Date: {data['date']}")
    print("Exchange rates:")
    print(len(data["rates"]))
    for currency, rate in data["rates"].items():
        print(f"SGD to {currency}: {rate}")
        
