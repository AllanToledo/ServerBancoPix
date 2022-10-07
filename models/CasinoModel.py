import random

from UserModel import User


class Casino(object):
    def __init__(self, user: User):
        self.name = "Cassino Poço dos Desejos"
        self.cost = 300000
        self.sellCost = self.cost * 0.8
        self.award = 200000
        self.owner: User = user

    def changeOwner(self, user: User):
        self.owner = user

    def bet(self):
        ball = random.choice(list(range(10)))
        return ball in list(range(3))

    def getData(self):
        return {
            "owner": self.owner.name,
            "ownerUID": self.owner.uid,
            "cost": self.cost,
            "award": self.award
        }
