class User:
    def __init__(self,email,name,password):
        self.email = email
        self.name = name
        self.password = password

class Account:
    def __init__(self,Email,AccountName,NameOnCard,Amount):
        self.Email = Email
        self.AccountName = AccountName
        self.NameOnCard = NameOnCard
        self.Amount = Amount

class SpendingAccount:
    def __init__(self, AccountName,Approval,RequestEmail):
        self.AccountName = AccountName
        self.Approval = Approval
        self.RequestEmail = RequestEmail
 