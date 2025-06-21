class User:
    def __init__(self,email,name,password):
        self.email = email
        self.name = name
        self.password = password

class Account:
    def __init__(self,AccountID,Email,AccountName,Amount):
        self.AccountID = AccountID
        self.Email = Email
        self.AccountName = AccountName
        self.Amount = Amount

class SpendingAccount:
    def __init__(self, AccountName,Approval,RequestEmail):
        self.AccountName = AccountName
        self.Approval = Approval
        self.RequestEmail = RequestEmail
 