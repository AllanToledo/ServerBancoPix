import time


class Transaction:
    def __init__(self, quantity: int, origin, receiver, type="Transferência Monetária"):
        self.origin: User = origin
        self.receiver: User = receiver
        self.quantity = quantity
        self.type = type
        self.date = round(time.time() * 1000)

    def getData(self):
        return {
            "receiver": self.receiver.name,
            "receiverUID": self.receiver.uid,
            "origin": self.origin.name,
            "originUID": self.origin.uid,
            "quantity": self.quantity,
            "type": self.type,
            "date": self.date
        }


class User(object):
    def __init__(self, money, name, uid):
        self.money = money
        self.name = name
        self.uid = uid
        self._transactions: list[Transaction] = []

    def addTransaction(self, transaction):
        self._transactions.append(transaction)

    def getTransactions(self):
        return self._transactions[:]
