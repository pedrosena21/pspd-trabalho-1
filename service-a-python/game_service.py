import grpc
from concurrent import futures
import bingo_pb2
import bingo_pb2_grpc
import uuid
import random
import os
from prometheus_client import start_http_server, Counter, Histogram

# ==========================================
# MÉTRICAS PROMETHEUS
# ==========================================

# Métricas de Negócio
GAMES_CREATED = Counter('games_created_total', 'Total number of games created')
PLAYERS_REGISTERED = Counter('players_registered_total', 'Total number of players registered')
NUMBERS_DRAWN = Counter('numbers_drawn_total', 'Total number of numbers drawn')
BINGO_CQRS = Counter('bingo_checked_total', 'Total number of bingo checks')

GRPC_REQUEST_LATENCY = Histogram(
    'grpc_request_duration_seconds',
    'Duration of gRPC requests in seconds',
    ['method', 'status']
)

class Game:
    def __init__(self, game_id, game_name):
        self.game_id = game_id
        self.game_name = game_name
        self.players = {}
        self.drawn_numbers = []

    def register_player(self, player_name):
        player_id = str(uuid.uuid4())
        card = random.sample(range(1, 76), 24)
        self.players[player_id] = {"name": player_name, "card": card}
        return player_id, card

class GameServiceServicer(bingo_pb2_grpc.GameServiceServicer):
    def __init__(self, validation_stub):
        self.games = {}
        self.validation_stub = validation_stub

    @GRPC_REQUEST_LATENCY.labels(method='CreateGame', status='ok').time()
    def CreateGame(self, request, context):
        game_id = str(uuid.uuid4())
        self.games[game_id] = Game(game_id, request.game_name)

        GAMES_CREATED.inc()

        print(f"\n[GAME SERVICE] ✓ Jogo criado: {request.game_name}")
        print(f"  Game ID: {game_id}\n")
        return bingo_pb2.CreateGameResponse(game_id=game_id)

    @GRPC_REQUEST_LATENCY.labels(method='RegisterPlayer', status='ok').time()
    def RegisterPlayer(self, request, context):
        if request.game_id not in self.games:
            print(f"[GAME SERVICE] ❌ Jogo {request.game_id} não encontrado")
            return bingo_pb2.RegisterPlayerResponse(success=False)

        game = self.games[request.game_id]
        player_id, card = game.register_player(request.player_name)

        PLAYERS_REGISTERED.inc()

        print(f"\n[GAME SERVICE] ✓ Jogador registrado: {request.player_name}")

        try:
            validation_request = bingo_pb2.RegisterCardRequest(
                player_id=player_id,
                card_numbers=card
            )
            response = self.validation_stub.RegisterCard(validation_request)
            if response.success:
                print(f"[GAME SERVICE] ✓ Cartela registrada no ValidationService")
            else:
                print(f"[GAME SERVICE] ⚠️  Erro ao registrar cartela no ValidationService")
        except grpc.RpcError as e:
            print(f"[GAME SERVICE] ❌ Erro de comunicação com ValidationService: {e}")

        return bingo_pb2.RegisterPlayerResponse(
            player_id=player_id,
            card_numbers=card,
            success=True
        )

    @GRPC_REQUEST_LATENCY.labels(method='DrawNumber', status='ok').time()
    def DrawNumber(self, request, context):
        if request.game_id not in self.games:
            return bingo_pb2.DrawNumberResponse(success=False)

        game = self.games[request.game_id]

        if len(game.drawn_numbers) >= 75:
            return bingo_pb2.DrawNumberResponse(success=False)

        number = random.randint(1, 75)
        while number in game.drawn_numbers:
            number = random.randint(1, 75)

        game.drawn_numbers.append(number)

        NUMBERS_DRAWN.inc()

        print(f"[GAME SERVICE] 🎲 Número sorteado: {number}")
        return bingo_pb2.DrawNumberResponse(number=number, success=True)

    def MarkNumber(self, request, context):
        if request.game_id not in self.games:
            return bingo_pb2.MarkNumberResponse(success=False)

        game = self.games[request.game_id]
        if request.number not in game.drawn_numbers:
            return bingo_pb2.MarkNumberResponse(success=False)

        try:
            validation_response = self.validation_stub.ValidateNumber(
                bingo_pb2.ValidateNumberRequest(
                    player_id=request.player_id,
                    number=request.number
                )
            )
            return bingo_pb2.MarkNumberResponse(success=validation_response.success)
        except grpc.RpcError:
            return bingo_pb2.MarkNumberResponse(success=False)

    def CheckBingo(self, request, context):
        BINGO_CQRS.inc()

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
            if validation_response.bingo:
                 print(f"[GAME SERVICE] 🏆 BINGO confirmado para {request.player_id}!")

            return bingo_pb2.CheckBingoResponse(bingo=validation_response.bingo)
        except grpc.RpcError:
            return bingo_pb2.CheckBingoResponse(bingo=False)

def serve():
    print("[GAME SERVICE] 📊 Iniciando servidor de métricas na porta 8001...")
    start_http_server(8001)

    validation_addr = os.getenv('VALIDATION_SERVICE_ADDR', 'validation-server-service:50052')
    print(f"[GAME SERVICE] Conectando ao ValidationService em {validation_addr}...")

    channel = grpc.insecure_channel(validation_addr)
    validation_stub = bingo_pb2_grpc.ValidationServiceStub(channel)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    bingo_pb2_grpc.add_GameServiceServicer_to_server(
        GameServiceServicer(validation_stub),
        server
    )
    server.add_insecure_port('[::]:50051')
    server.start()
    print("[GAME SERVICE] 🚀 Servidor gRPC rodando na porta 50051...\n")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
