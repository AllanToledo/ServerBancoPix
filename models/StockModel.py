class Stock(object):
    def __init__(self, sid, name: str, basePrice: int, position: int):
        self.sid = sid
        self.name = name,
        self.basePrice = basePrice
        self.value = 1.0
        self.position = position
        self.lastValues: list[float] = []

    def low(self, quantity):
        self.lastValues.append(self.value)
        if len(self.lastValues) > 20:
            self.lastValues.pop(0)
        self.value -= quantity / 100

    def up(self, quantity):
        self.lastValues.append(self.value)
        if len(self.lastValues) > 20:
            self.lastValues.pop(0)
        self.value += quantity / 100

    def getPrice(self):
        return self.basePrice * self.value

    def getValue(self):
        return self.value

    def getBasePrice(self):
        return self.basePrice

    def getData(self):
        return {
            "sid": self.sid,
            "name": self.name,
            "value": self.value,
            "price": self.getPrice(),
            "position": self.position,
            "last": self.lastValues
        }
