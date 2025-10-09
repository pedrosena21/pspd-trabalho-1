import grpc
from concurrent import futures
import bingo_pb2
import bingo_pb2_grpc

class ValidationServiceServicer(bingo_pb2_grpc.ValidationServiceServicer):
    def __init__(self):
        self.players = {}  # player_id -> {"card": [...], "marked": set()}

    def RegisterCard(self, request, context):
        self.players[request.player_id] = {"card": list(request.card_numbers), "marked": set()}
        print(f"[VALIDATION SERVICE] Cartela registrada para {request.player_id}: {request.card_numbers}")
        return bingo_pb2.RegisterCardResponse(success=True)

    def ValidateNumber(self, request, context):
        if request.player_id in self.players:
            card = self.players[request.player_id]["card"]
            if request.number in card:
                self.players[request.player_id]["marked"].add(request.number)
                return bingo_pb2.ValidateNumberResponse(success=True)
        return bingo_pb2.ValidateNumberResponse(success=False)

    def ValidateBingo(self, request, context):
        if request.player_id in self.players:
            card = set(self.players[request.player_id]["card"])
            marked = set(self.players[request.player_id]["marked"])
            if card.issubset(marked):
                return bingo_pb2.ValidateBingoResponse(bingo=True)
        return bingo_pb2.ValidateBingoResponse(bingo=False)

    def GetCard(self, request, context):
        if request.player_id in self.players:
            return bingo_pb2.GetCardResponse(card_numbers=self.players[request.player_id]["card"])
        return bingo_pb2.GetCardResponse(card_numbers=[])

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    bingo_pb2_grpc.add_ValidationServiceServicer_to_server(ValidationServiceServicer(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    print("[VALIDATION SERVICE] Rodando na porta 50052...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()

