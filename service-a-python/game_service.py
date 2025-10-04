import grpc
from concurrent import futures
import bingo_pb2
import bingo_pb2_grpc
import uuid
import random

class Game:
    def __init__(self, game_id, game_name):
        self.game_id = game_id
        self.game_name = game_name
        self.players = {}
        self.drawn_numbers = []

    def register_player(self, player_name):
        player_id = str(uuid.uuid4())
        card = random.sample(range(1, 76), 24)  # Cartela com 24 números
        self.players[player_id] = {"name": player_name, "card": card}
        return player_id, card

class GameServiceServicer(bingo_pb2_grpc.GameServiceServicer):
    def __init__(self, validation_stub):
        self.games = {}
        self.validation_stub = validation_stub

    def CreateGame(self, request, context):
        print('JOGO CRIADO', request)
        game_id = str(uuid.uuid4())
        self.games[game_id] = Game(game_id, request.game_name)
        print(f"[GAME SERVICE] Jogo criado: {request.game_name} ({game_id})")
        return bingo_pb2.CreateGameResponse(game_id=game_id)

    def RegisterPlayer(self, request, context):
        if request.game_id not in self.games:
            return bingo_pb2.RegisterPlayerResponse(success=False)

        game = self.games[request.game_id]
        player_id, card = game.register_player(request.player_name)

        print(f"[GAME SERVICE] Jogador registrado: {request.player_name} ({player_id})")
        print(f"  Cartela: {card}")

        # Notifica o Serviço B para registrar a cartela
        try:
            validation_request = bingo_pb2.RegisterCardRequest(
                player_id=player_id,
                card_numbers=card
            )
            self.validation_stub.RegisterCard(validation_request)
            print(f"[GAME SERVICE] Cartela registrada no ValidationService para {player_id}")
        except grpc.RpcError as e:
            print(f"[GAME SERVICE] Erro ao registrar cartela no ValidationService: {e}")

        return bingo_pb2.RegisterPlayerResponse(
            player_id=player_id,
            card_numbers=card,
            success=True
        )

    def DrawNumber(self, request, context):
        if request.game_id not in self.games:
            return bingo_pb2.DrawNumberResponse(success=False)

        game = self.games[request.game_id]
        number = random.randint(1, 75)
        while number in game.drawn_numbers:
            number = random.randint(1, 75)
        game.drawn_numbers.append(number)

        print(f"[GAME SERVICE] Número sorteado: {number}")
        return bingo_pb2.DrawNumberResponse(number=number, success=True)

    def MarkNumber(self, request, context):
        try:
            validation_response = self.validation_stub.ValidateNumber(
                bingo_pb2.ValidateNumberRequest(
                    player_id=request.player_id,
                    number=request.number
                )
            )
            if validation_response.success:
                print(f"[GAME SERVICE] Número {request.number} marcado para {request.player_id}")
            else:
                print(f"[GAME SERVICE] Número {request.number} NÃO encontrado para {request.player_id}")
            return bingo_pb2.MarkNumberResponse(success=validation_response.success)
        except grpc.RpcError as e:
            print(f"[GAME SERVICE] Erro ao validar número: {e}")
            return bingo_pb2.MarkNumberResponse(success=False)

    def CheckBingo(self, request, context):
        if request.game_id not in self.games:
            return bingo_pb2.CheckBingoResponse(bingo=False)

        game = self.games[request.game_id]
        try:
            validation_response = self.validation_stub.ValidateBingo(
                bingo_pb2.ValidateBingoRequest(
                    player_id=request.player_id,
                    numbers=game.drawn_numbers
                )
            )
            print(f"[GAME SERVICE] Bingo verificado para {request.player_id}: {validation_response.bingo}")
            return bingo_pb2.CheckBingoResponse(bingo=validation_response.bingo)
        except grpc.RpcError as e:
            print(f"[GAME SERVICE] Erro ao verificar bingo: {e}")
            return bingo_pb2.CheckBingoResponse(bingo=False)

def serve():
    channel = grpc.insecure_channel('localhost:50052')
    validation_stub = bingo_pb2_grpc.ValidationServiceStub(channel)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    bingo_pb2_grpc.add_GameServiceServicer_to_server(GameServiceServicer(validation_stub), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("[GAME SERVICE] Rodando na porta 50051...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()

