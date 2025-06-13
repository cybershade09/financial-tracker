import sqlite3
sql = """
CREATE TABLE User(
	Email TEXT PRIMARY KEY,
	Name TEXT NOT NULL,
	Password TEXT NOT NULL
);

CREATE TABLE SpendingAccount(
	AccountName TEXT PRIMARY KEY,
	Approval BOOLEAN NOT NULL,
	RequestEmail TEXT NOT NULL,
	FOREIGN KEY (RequestEmail) REFERENCES User(Email)
);

CREATE TABLE Account(
	AccountID INTEGER PRIMARY KEY AUTOINCREMENT,
	Email TEXT NOT NULL,
	AccountName TEXT NOT NULL,
	FOREIGN KEY (Email) REFERENCES User(Email),
	FOREIGN KEY (AccountName) REFERENCES SpendingAccount(AccountName)
);

CREATE TABLE Transactions(
	TransactionID INTEGER PRIMARY KEY AUTOINCREMENT,
	AccountID INTEGER NOT NULL,
	Date TEXT NOT NULL,
	Amount REAL NOT NULL,
	Description TEXT,
	Category TEXT,
	IsExpense BOOLEAN NOT NULL,
	FOREIGN KEY (AccountID) REFERENCES Account(AccountID)
);

CREATE TABLE InvestmentType(
	InvestmentHeader TEXT PRIMARY KEY,
	Category TEXT NOT NULL,
	Price REAL NOT NULL,
	DateUpdated TEXT NOT NULL
);

CREATE TABLE Investment(
	Email TEXT NOT NULL,
	InvestmentHeader TEXT NOT NULL,
	Quantity REAL NOT NULL,
	PRIMARY KEY (Email, InvestmentHeader),
	FOREIGN KEY (Email) REFERENCES User(Email),
	FOREIGN KEY (InvestmentHeader) REFERENCES InvestmentType(InvestmentHeader)
);

CREATE TABLE ForexType(
	ForeignCountry TEXT PRIMARY KEY,
	Rate REAL NOT NULL,
	DateUpdated TEXT NOT NULL
);

CREATE TABLE Forex(
	Email TEXT NOT NULL,
	ForeignCountry TEXT NOT NULL,
	Amount REAL NOT NULL,
	PRIMARY KEY (Email, ForeignCountry),
	FOREIGN KEY (Email) REFERENCES User(Email),
	FOREIGN KEY (ForeignCountry) REFERENCES ForexType(ForeignCountry)
);

CREATE TABLE NetWorthHistory(
	Email TEXT NOT NULL,
	DateUploaded TEXT NOT NULL,
	NetWorth REAL NOT NULL,
	PRIMARY KEY (Email, DateUploaded),
	FOREIGN KEY (Email) REFERENCES User(Email)
);
"""

db = sqlite3.connect("database.db")
for s in sql.split(";"):
	db.execute(s)
db.commit()
db.close()