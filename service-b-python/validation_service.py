import grpc
from concurrent import futures
import bingo_pb2
import bingo_pb2_grpc
from prometheus_client import start_http_server, Counter, Histogram

# ==========================================
# MÉTRICAS PROMETHEUS (Padrão Service B)
# ==========================================

CARDS_REGISTERED = Counter('validation_cards_registered_total', 'Total number of cards registered in validation service')
NUMBERS_VALIDATED = Counter('validation_numbers_checked_total', 'Total number of attempts to validate a number', ['result']) # labels: valid, invalid
BINGO_VALIDATED = Counter('validation_bingo_checked_total', 'Total number of bingo validations performed', ['result']) # labels: winner, loser

GRPC_REQUEST_LATENCY = Histogram(
    'validation_grpc_request_duration_seconds',
    'Duration of Validation gRPC requests in seconds',
    ['method', 'status']
)

class ValidationServiceServicer(bingo_pb2_grpc.ValidationServiceServicer):
    def __init__(self):
        self.players = {}  # player_id -> {"card": [...], "marked": set()}

    @GRPC_REQUEST_LATENCY.labels(method='RegisterCard', status='ok').time()
    def RegisterCard(self, request, context):
        self.players[request.player_id] = {"card": list(request.card_numbers), "marked": set()}
        
        CARDS_REGISTERED.inc()
        
        print(f"[VALIDATION SERVICE] 📝 Cartela registrada para {request.player_id}")
        return bingo_pb2.RegisterCardResponse(success=True)

    @GRPC_REQUEST_LATENCY.labels(method='ValidateNumber', status='ok').time()
    def ValidateNumber(self, request, context):
        is_valid = False
        if request.player_id in self.players:
            card = self.players[request.player_id]["card"]
            if request.number in card:
                self.players[request.player_id]["marked"].add(request.number)
                is_valid = True
        
        result_label = "valid" if is_valid else "invalid"
        NUMBERS_VALIDATED.labels(result=result_label).inc()

        return bingo_pb2.ValidateNumberResponse(success=is_valid)

    @GRPC_REQUEST_LATENCY.labels(method='ValidateBingo', status='ok').time()
    def ValidateBingo(self, request, context):
        is_bingo = False
        if request.player_id in self.players:
            card = set(self.players[request.player_id]["card"])
            marked = set(self.players[request.player_id]["marked"])
            
            if card.issubset(marked):
                is_bingo = True

        result_label = "winner" if is_bingo else "loser"
        BINGO_VALIDATED.labels(result=result_label).inc()

        if is_bingo:
            print(f"[VALIDATION SERVICE] 🏆 BINGO VALIDADO para {request.player_id}!")

        return bingo_pb2.ValidateBingoResponse(bingo=is_bingo)

    @GRPC_REQUEST_LATENCY.labels(method='GetCard', status='ok').time()
    def GetCard(self, request, context):
        if request.player_id in self.players:
            return bingo_pb2.GetCardResponse(card_numbers=self.players[request.player_id]["card"])
        return bingo_pb2.GetCardResponse(card_numbers=[])

def serve():
    print("[VALIDATION SERVICE] 📊 Iniciando servidor de métricas na porta 8002...")
    start_http_server(8002)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    bingo_pb2_grpc.add_ValidationServiceServicer_to_server(ValidationServiceServicer(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    print("[VALIDATION SERVICE] 🚀 Rodando gRPC na porta 50052...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()