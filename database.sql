CREATE TABLE User(
    Email TEXT PRIMARY KEY,
    Name TEXT NOT NULL,
    Password TEXT NOT NULL
);

CREATE TABLE SpendingAccount(
    AccountName TEXT PRIMARY KEY,
    Approval INTEGER NOT NULL,
    RequestEmail TEXT NOT NULL,
    FOREIGN KEY (RequestEmail) REFERENCES User(Email)
);

CREATE TABLE Investment(
    Email TEXT NOT NULL,
    InvestmentHeader TEXT NOT NULL,
    Quantity REAL NOT NULL,
    PRIMARY KEY (Email, InvestmentHeader),
    FOREIGN KEY (Email) REFERENCES User(Email),
);

CREATE TABLE Forex(
    Email TEXT NOT NULL,
    ForeignCountry TEXT NOT NULL,
    Amount REAL NOT NULL,
    PRIMARY KEY (Email, ForeignCountry),
    FOREIGN KEY (Email) REFERENCES User(Email)
);
                                             
CREATE TABLE Account(
    Email TEXT NOT NULL,
    AccountName TEXT NOT NULL,
    NameOnCard TEXT NOT NULL,
    Amount REAL NOT NULL,
    FOREIGN KEY (Email) REFERENCES User(Email),
    FOREIGN KEY (AccountName) REFERENCES SpendingAccount(AccountName),
    PRIMARY KEY(Email,AccountName,NameOnCard)
);

CREATE TABLE AccountIDMap(
    AccountID INTEGER PRIMARY KEY AUTOINCREMENT,
    Email TEXT NOT NULL,
    AccountName TEXT NOT NULL,
    NameOnCard TEXT NOT NULL,
    FOREIGN KEY(Email,AccountName,NameOnCard) REFERENCES Account(Email,AccountName,NameOnCard)
);

CREATE TABLE Transactions(
    TransactionID TEXT PRIMARY KEY NOT NULL,
    AccountID INTEGER NOT NULL,
    Date TEXT NOT NULL,
    Amount REAL NOT NULL,
    Description TEXT,
    Category TEXT,
    FOREIGN KEY (AccountID) REFERENCES AccountIDMap(AccountID)
);

CREATE TABLE TransactionType(
    TransactionID TEXT NOT NULL,
    IsExpense INTEGER,
    FOREIGN KEY(TransactionID) REFERENCES Transactions(TransactionID)
    PRIMARY KEY(TransactionID)
);
