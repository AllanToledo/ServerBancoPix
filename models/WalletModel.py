from StockModel import Stock


class Wallet(object):
    def __init__(self, stock: Stock):
        self.stock = stock
        self.quantity = 0

    def buy(self, quantity):
        self.quantity += quantity

    def sell(self, quantity):
        self.quantity -= quantity

    def getData(self):
        return {"sid": self.stock.sid, "name": self.stock.name, "quantity": self.quantity}