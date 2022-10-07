from UserModel import User


class Bank(User):
    def __init__(self):
        User.__init__(self, 1e9, "Banco", -1)
