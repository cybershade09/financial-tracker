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
    
    def to_dict(self):
        return {"Email":self.Email,"AccountName":self.AccountName,"NameOnCard":self.NameOnCard,"Amount":self.Amount}

    @staticmethod
    def from_dict(data):
        return Account(data["Email"],data["AccountName"],data["NameOnCard"],data["Amount"])
class SpendingAccount:
    def __init__(self, AccountName,Approval,RequestEmail):
        self.AccountName = AccountName
        self.Approval = Approval
        self.RequestEmail = RequestEmail
 
class Transaction:
    def __init__(self,TransactionID,AccountID,Date,Amount,Description,Category,IsExpense):
        self.TransactionID = TransactionID
        self.AccountID = AccountID
        self.Date = Date
        self.Amount = Amount
        self.Description = Description
        self.Category = Category
        self.IsExpense = IsExpense