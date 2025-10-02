import grpc
from concurrent import futures
import cartela_pb2
import cartela_pb2_grpc
import random
import numpy as np
from google.protobuf import empty_pb2

def generate_cartela():
    cartela = np.zeros((5, 5), dtype=int)
    for i in range(0, 5):
        for j in range(0, 5):
            cartela[i][j] = random.randint(1, 100)
    
    return cartela

class CartelaService(cartela_pb2_grpc.cartelaServiceServicer):
    def SendVencedor(self, request, context):
        return cartela_pb2.Vencedor(usuario=1)

    def SendCartela(self, request, context):
        return cartela_pb2.MessageList(messages=[
            cartela_pb2.Message(usuario=1, campo=generate_cartela()),
            cartela_pb2.Message(usuario=2, campo=generate_cartela())
        ])

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    cartela_pb2_grpc.add_cartelaServiceServicer_to_server(CartelaService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
