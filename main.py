import time
import random

from UserModel import User, Transaction
from BankModel import Bank
from ResultModel import Result
from flask import Flask
from flask_cors import CORS, cross_origin
from flask_restful import Resource, Api, reqparse
from flask_socketio import SocketIO

from CasinoModel import Casino
from PlayerModel import Player
from StockModel import Stock
from WalletModel import Wallet

app = Flask(__name__)
app.config["SECRET_KEY"] = "password"
cors = CORS(app, resources={r"/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'
api = Api(app)
socketio = SocketIO(app, cors_allowed_origins="*")

parser = reqparse.RequestParser()
bank = Bank()
casino = Casino(bank)
players: list[Player] = []
stocks: list[Stock] = [
    Stock(0, "Companhia de Força e Luz", 100_000, 4),
    Stock(1, "Companhia de Água e Saneamento", 100_000, 9),
    Stock(2, "Companhia Petrolífera", 100_000, 15),
    Stock(3, "Companhia de Mineração", 100_000, 23),
    Stock(4, "Créditos de Carbono", 100_000, 30),
    Stock(5, "Pontocom", 100_000, 37),
]
transactions: list[dict] = []


@socketio.on('message', namespace='/')
def handle_message(message):
    print('message received: ' + message)


class Create(Resource):
    def post(self):
        parser.add_argument("name")
        args = parser.parse_args()
        name = args["name"]
        for player in players:
            if player.name == name:
                return Result.error("Nome já esta em uso.")
        if name == bank.name:
            return Result.error("Nome reservado.")
        money = int(2_558_000)
        if len(players) > 0:
            player = Player(money, name, players[-1].uid + 1, bank)
        else:
            player = Player(money, name, 0, bank)

        for stock in stocks:
            player.wallets.append(Wallet(stock))
        players.append(player)
        socketio.send("update", namespace='/', broadcast=True)
        return Result.successful({"uid": player.uid})


class Login(Resource):
    def get(self):
        parser.add_argument("password")
        args = parser.parse_args()
        password = args["password"]
        for player in players:
            if player.password == password:
                return Result.successful({"uid": player.uid})

        return Result.error("Código inválido")


class ListPlayers(Resource):
    def get(self):
        result = [player.getData() for player in players]
        return Result.successful({"players": result})


class Data(Resource):
    def get(self):
        parser.add_argument("uid")
        args = parser.parse_args()
        uid: int = int(args["uid"])
        for player in players:
            if player.uid == uid:
                return Result.successful({"data": player.getData()})
        return Result.error("Código inválido")


class Delete(Resource):
    def delete(self):
        parser.add_argument("uid")
        args = parser.parse_args()
        uid: int = int(args["uid"])
        global players
        players = list(filter(lambda player: player.uid != uid, players))
        result = [player.getData() for player in players]
        socketio.send("update", namespace='/', broadcast=True)
        return Result.successful({"players": result})


class Turn(Resource):
    def get(self):
        for player in players:
            if player.turn:
                return Result.successful({"player": player.getData()})

        player = random.choice(players)
        player.turn = True
        player.dice = 1
        socketio.send("update", namespace='/', broadcast=True)
        return Result.successful({"player": player.getData()})

    def post(self):
        parser.add_argument("uid")
        args = parser.parse_args()
        uid: int = int(args["uid"])
        nextPlayer = None
        for (index, player) in enumerate(players):
            if player.uid == uid:
                if not player.turn:
                    return Result.error("Não é a sua vez de jogar")
                if player.dice > 0:
                    return Result.error("Você precisa jogar antes de passar a sua vez")
                if player.position == 31 and player.tax > 0:
                    return Result.error("Irmão, se tem que pagar os impostos.")
                nextIndex = index
                while True:
                    nextIndex = 0 if nextIndex == (len(players) - 1) else nextIndex + 1
                    nextPlayer = players[nextIndex]
                    print(nextIndex)
                    if not nextPlayer.lost:
                        break

        for player in players:
            player.turn = False

        for stock in stocks:
            stock.low(1)

        nextPlayer.turn = True
        nextPlayer.dice += 1
        socketio.send("update", namespace='/', broadcast=True)
        return Result.successful({"data": nextPlayer.getData()})


class Bet(Resource):
    def post(self):
        parser.add_argument("uid")
        args = parser.parse_args()
        uid: int = int(args["uid"])
        player: Player = None
        for p in players:
            if p.uid == uid:
                player = p

        if casino.owner.uid == -1:
            return Result.error("Casino não está aceitando apostas.")

        if player.money < casino.award:
            return Result.error("Saldo insuficiente.")

        if player.position != 11:
            return Result.error("Precisa estar na casa do Cassino.")

        betResult = casino.bet()

        if betResult:
            player.money += casino.award
            if casino.owner is Player:
                casino.owner.money -= casino.award
            transaction = Transaction(
                casino.award,
                receiver=player,
                origin=casino.owner,
                type="Aposta no Cassino"
            )
            player.addTransaction(transaction)
            casino.owner.addTransaction(transaction)
            socketio.send("update", namespace='/', broadcast=True)
            return Result.successful({"message": "Você ganhou!"})
        else:
            player.money -= casino.award
            if casino.owner is Player:
                casino.owner.money += casino.award
            transaction = Transaction(
                receiver=casino.owner,
                origin=player,
                quantity=casino.award,
                type="Aposta no Cassino"
            )
            player.addTransaction(transaction)
            casino.owner.addTransaction(transaction)
            socketio.send("update", namespace='/', broadcast=True)
            return Result.successful({"message": "O Casino ganhou."})


class CasinoCompany(Resource):
    def get(self):
        return casino.getData()

    def post(self):
        parser.add_argument("uid")
        parser.add_argument("operation")
        args = parser.parse_args()
        uid: int = int(args["uid"])
        operation: str = str(args["operation"])
        if casino.owner.uid > -1 and casino.owner.uid != uid:
            return Result.error("O Cassino está sob posse de um player.")
        if operation == "sell" and casino.owner.uid != uid:
            return Result.error("O Cassino está sob posse de um player.")
        for player in players:
            if player.uid == uid:
                if operation == "sell":
                    cost = casino.sellCost
                    player.money += cost
                    casino.changeOwner(bank)
                    transaction = Transaction(
                        receiver=player,
                        origin=bank,
                        quantity=cost,
                        type="Venda do Cassino"
                    )
                    player.addTransaction(transaction)
                    bank.addTransaction(transaction)
                    socketio.send("update", namespace='/', broadcast=True)
                    return Result.successful()
                if operation == "buy":
                    if player.position != 11:
                        return Result.error("Precisa estar na casa do Casino para comprar")
                    if player.money < casino.cost:
                        return Result.error("Saldo insuficiente.")
                    player.money -= casino.cost
                    casino.changeOwner(player)
                    transaction = Transaction(
                        receiver=bank,
                        origin=player,
                        quantity=casino.cost,
                        type="Compra do Cassino"
                    )
                    bank.addTransaction(transaction)
                    player.addTransaction(transaction)
                    socketio.send("update", namespace='/', broadcast=True)
                    return Result.successful()


class Broker(Resource):
    def get(self):
        parser.add_argument("uid")
        args = parser.parse_args()
        uid: int = int(args["uid"] if args["uid"] is not None else -1)
        if uid == -1:
            return Result.successful({"stocks": [stock.getData() for stock in stocks]})
        for player in players:
            if player.uid == uid:
                return Result.successful({"wallet": [wallet.getData() for wallet in player.wallets]})

    def post(self):
        parser.add_argument("uid")
        parser.add_argument("quantity")
        parser.add_argument("sid")
        parser.add_argument("operation")
        args = parser.parse_args()
        uid: int = int(args["uid"])
        quantity: int = int(args["quantity"])
        sid: int = int(args["sid"])
        operation: str = str(args["operation"])
        for player in players:
            if player.uid == uid:
                if operation == "buy":
                    result = player.buyStocks(sid, quantity)
                    if result["result"] == "OK":
                        transaction = Transaction(
                            receiver=bank,
                            origin=player,
                            quantity=result["data"]["cost"],
                            type="Compra de ações"
                        )
                        bank.addTransaction(transaction)
                        player.addTransaction(transaction)
                    socketio.send("update", namespace='/', broadcast=True)
                    return result
                elif operation == "sell":
                    result = player.sellStocks(sid, quantity)
                    if result["result"] == "OK":
                        transaction = Transaction(
                            receiver=player,
                            origin=bank,
                            quantity=result["data"]["cost"],
                            type="Venda de ações"
                        )
                        bank.addTransaction(transaction)
                        player.addTransaction(transaction)
                    socketio.send("update", namespace='/', broadcast=True)
                    return result
                return Result.error("Operação inválida")
        return Result.error("UID inválido")


class Dice(Resource):
    def post(self):
        parser.add_argument("uid")
        args = parser.parse_args()
        uid: int = int(args["uid"])
        for player in players:
            if player.uid == uid:
                if not player.turn:
                    return Result.error("Não é a sua vez de jogar")
                if player.dice < 1:
                    return Result.error("Você não tem mais jogadas restantes. Passe a vez.")
                if player.position == 31 and player.tax > 0 and not player.habeas_corpus:
                    return Result.error("Irmão, se tem que pagar os impostos.")

                if player.habeas_corpus:
                    player.habeas_corpus = False

                player.dice -= 1
                firstDice = random.choice(list(range(1, 7)))
                time.sleep(0.05)
                secondDice = random.choice(list(range(1, 7)))

                if firstDice == secondDice:
                    player.dice += 1
                distance = firstDice + secondDice
                player.move(distance)

                for stock in stocks:
                    if stock.position == player.position:
                        stock.up(20)
                socketio.send("update", namespace='/', broadcast=True)
                return Result.successful({"dices": [firstDice, secondDice]})


class Tax(Resource):
    def get(self):
        parser.add_argument("uid")
        args = parser.parse_args()
        uid: int = int(args["uid"])
        for player in players:
            if player.uid == uid:
                cost = player.tax
                mulct = player.tax * 0.5 if player.position == 31 else 0
                return Result.successful({"cost": cost, "mulct": mulct})

    def post(self):
        parser.add_argument("uid")
        args = parser.parse_args()
        uid: int = int(args["uid"])
        for player in players:
            if player.uid == uid:
                cost = player.tax
                if cost < 1:
                    return Result.error("Seus impostos estão em dia")
                mulct = player.tax * 0.5 if player.position == 31 else 0
                quantity = cost + mulct
                player.money -= quantity
                player.tax = 0
                transaction = Transaction(
                    receiver=bank,
                    origin=player,
                    quantity=quantity,
                    type="Imposto de Renda"
                )
                player.addTransaction(transaction)
                bank.addTransaction(transaction)
                socketio.send("update", namespace='/', broadcast=True)
                return Result.successful()


class Transactions(Resource):
    def get(self):
        parser.add_argument("uid")
        args = parser.parse_args()
        uid: int = int(args["uid"] if args["uid"] is not None else -1)
        if uid == -1:
            result = [transaction.getData() for transaction in bank.getTransactions()]
            result.reverse()
            return Result.successful({"transactions": result})
        for player in players:
            if player.uid == uid:
                result = [transaction.getData() for transaction in player.getTransactions()]
                result.reverse()
                return Result.successful({"transactions": result})
        return Result.error("UID inválido")

    def post(self):
        parser.add_argument("origin")
        parser.add_argument("quantity")
        parser.add_argument("receiver")
        args = parser.parse_args()
        origin: int = int(args["origin"])
        receiver: int = int(args["receiver"])
        try:
            quantity: int = int(args["quantity"])
        except ValueError as e:
            return Result.error("Quantidade precisa ser um valor inteiro.")

        user_origin: User = bank
        user_receiver: User = bank
        for player in players:
            if player.uid == origin:
                user_origin = player
            if player.uid == receiver:
                user_receiver = player

        if quantity < 1:
            return Result.error("Apenas valores maiores ou igual a 1")

        if quantity > user_origin.money:
            return Result.error("Dinheiro insuficiente")

        user_origin.money -= quantity
        user_receiver.money += quantity

        transaction = Transaction(
            receiver=user_receiver,
            origin=user_origin,
            quantity=quantity,
        )
        user_origin.addTransaction(transaction)
        user_receiver.addTransaction(transaction)
        socketio.send("update", namespace='/', broadcast=True)
        return Result.successful()


class MovePlayer(Resource):
    def post(self):
        parser.add_argument("uid")
        parser.add_argument("position")
        args = parser.parse_args()
        uid: int = int(args["uid"])
        position: int = int(args["position"])
        for player in players:
            if player.uid == uid:
                player.position = position
                return Result.successful()
        return Result.error("UID inválido")


class HabeasCorpus(Resource):
    def post(self):
        parser.add_argument("uid")
        parser.add_argument("operation")
        args = parser.parse_args()
        uid: int = int(args["uid"])
        operation: bool = bool(args["operation"] == "true")
        for player in players:
            if player.uid == uid:
                player.habeas_corpus = operation
                socketio.send("update", namespace='/', broadcast=True)
                return Result.successful()
        return Result.error("UID inválido")


class LostGame(Resource):
    def post(self):
        parser.add_argument("uid")
        parser.add_argument("lost")
        args = parser.parse_args()
        uid: int = int(args["uid"])
        lost: bool = bool(args["lost"] == "true")
        for player in players:
            if player.uid == uid:
                player.lost = lost
                socketio.send("update", namespace='/', broadcast=True)
                return Result.successful()
        return Result.error("UID inválido")


# admin
api.add_resource(MovePlayer, "/move")
api.add_resource(Delete, "/delete")

api.add_resource(Broker, "/broker")
api.add_resource(Bet, "/bet")
api.add_resource(CasinoCompany, "/casino")
api.add_resource(Create, "/create")
api.add_resource(Data, "/data")
api.add_resource(Dice, "/dice")
api.add_resource(HabeasCorpus, "/habeascorpus")
api.add_resource(ListPlayers, "/players")
api.add_resource(Login, "/login")
api.add_resource(LostGame, "/lost")
api.add_resource(Tax, "/tax")
api.add_resource(Turn, "/turn")
api.add_resource(Transactions, "/transaction")

if __name__ == '__main__':
    configs = []
    with open("config.txt", "r") as file:
        configs = file.read().split("\n")
    # app.run(host=configs[0])
    socketio.run(app, host=configs[0], port=5000)
