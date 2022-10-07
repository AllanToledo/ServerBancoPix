import random
import string

from ResultModel import Result
from UserModel import User, Transaction
from WalletModel import Wallet


def get_random_string(length) -> str:
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


class Player(User):
    def __init__(self, money: int, name: str, uid: int, bank: User):
        User.__init__(self, money, name, uid)
        self.bank = bank
        self.password = get_random_string(4)
        self.tax = 0
        self.lost = False
        self.turn = False
        self.position = 1
        self.lastPosition = 1
        self.dice = 0
        self.wallets: list[Wallet] = []
        self.habeas_corpus = False

    def move(self, positions):
        self.lastPosition = self.position
        self.position += positions
        if self.position > 40:
            self.addTransaction(Transaction(
                receiver=self,
                origin=self.bank,
                quantity=200_000,
                type="Pró Labore"
            ))
            self.money += 200_000
            self.tax += 50_000
            self.position -= 40

    def getData(self):
        return {
            "name": self.name,
            "money": self.money,
            "uid": self.uid,
            "lost": self.lost,
            "password": self.password,
            "turn": self.turn,
            "lastPosition": self.lastPosition,
            "position": self.position,
            "dice": self.dice,
            "habeas_corpus": self.habeas_corpus,
            "tax": self.tax
        }

    def buyStocks(self, sid, quantity):
        for wallet in self.wallets:
            if wallet.stock.sid == sid:
                cost = wallet.stock.getPrice() * quantity
                if self.money < cost:
                    return Result.error("Dinheiro insuficiente")
                self.money -= cost
                wallet.buy(quantity)
                return Result.successful({"stocks": [wallet.getData() for wallet in self.wallets], "cost": cost})

    def sellStocks(self, sid, quantity):
        for wallet in self.wallets:
            if wallet.stock.sid == sid:
                cost = wallet.stock.getPrice() * quantity
                if wallet.quantity < quantity:
                    return Result.error("Ações insuficientes")
                self.money += cost
                wallet.sell(quantity)
                return Result.successful({"stocks": [wallet.getData() for wallet in self.wallets], "cost": cost})

    def getStocks(self):
        return {
            "stocks": [wallet.getData() for wallet in self.wallets]
        }
