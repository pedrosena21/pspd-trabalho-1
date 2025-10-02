"""
Cliente de teste para o sistema de Bingo gRPC
Simula um jogador completo
"""

import grpc
import bingo_pb2
import bingo_pb2_grpc
import time
import threading


class BingoPlayer:
    def __init__(self, player_name, stub_address='localhost:50051'):
        self.player_name = player_name
        self.channel = grpc.insecure_channel(stub_address)
        self.stub = bingo_pb2_grpc.GameServiceStub(self.channel)

        self.player_id = None
        self.card = []
        self.marked = set()
        self.game_id = None

    def create_game(self, game_name="Bingo Test"):
        """Cria um novo jogo"""
        request = bingo_pb2.CreateGameRequest(game_name=game_name)
        response = self.stub.CreateGame(request)

        if response.game_id:  # só checa se veio um ID válido
            self.game_id = response.game_id
            print(f"✓ Jogo criado: {self.game_id}")
            return True
        else:
            print("✗ Erro: não foi possível criar o jogo")
            return False

    def register(self, game_id):
        """Registra o jogador no jogo"""
        self.game_id = game_id
        request = bingo_pb2.RegisterPlayerRequest(
            game_id=game_id,
            player_name=self.player_name
        )
        response = self.stub.RegisterPlayer(request)

        if response.success:
            self.player_id = response.player_id
            self.card = list(response.card_numbers)
            print(f"\n{'='*60}")
            print(f"Jogador: {self.player_name}")
            print(f"ID: {self.player_id}")
            print(f"Cartela: {self.card}")
            print(f"{'='*60}\n")
            return True
        return False

    def listen_drawing(self):
        """Escuta o sorteio de números (em thread separada)"""
        request = bingo_pb2.DrawNumberRequest(game_id=self.game_id)

        try:
            while True:
                number_drawn = self.stub.DrawNumber(request)
                if not number_drawn.success:
                    break

                number = number_drawn.number
                print(f"\n🎲 NÚMERO SORTEADO: {number}")

                # Verifica se tem o número na cartela
                if number in self.card and number not in self.marked:
                    self.mark_number(number)

                    # Verifica se completou o bingo
                    if len(self.marked) == len(self.card):
                        time.sleep(0.5)  # Pequeno delay
                        self.declare_bingo()
                        break

                time.sleep(1)  # Simula sorteio em intervalos

        except grpc.RpcError as e:
            print(f"Erro no sorteio: {e}")

    def mark_number(self, number):
        """Marca um número na cartela"""
        request = bingo_pb2.MarkNumberRequest(
            game_id=self.game_id,
            player_id=self.player_id,
            number=number
        )

        response = self.stub.MarkNumber(request)

        if response.success:
            self.marked.add(number)
            print(f"  ✓ {self.player_name} marcou o número {number} ({len(self.marked)}/{len(self.card)})")
        else:
            print(f"  ✗ Número {number} inválido ou não está na cartela")

    def declare_bingo(self):
        """Declara BINGO"""
        print(f"\n{'='*60}")
        print(f"🎉 {self.player_name} está declarando BINGO!")
        print(f"{'='*60}")

        request = bingo_pb2.CheckBingoRequest(
            game_id=self.game_id,
            player_id=self.player_id
        )

        response = self.stub.CheckBingo(request)

        if response.bingo:
            print(f"\n🏆 VITÓRIA! Bingo confirmado.")
        else:
            print(f"\n❌ Bingo inválido.")


def test_single_player():
    """Teste com um único jogador"""
    print("\n" + "="*60)
    print("TESTE: Jogador Único")
    print("="*60 + "\n")

    player = BingoPlayer("Alice")

    # Criar jogo
    if not player.create_game("Teste Single Player"):
        print("Erro ao criar jogo")
        return

    # Registrar
    if not player.register(player.game_id):
        print("Erro ao registrar jogador")
        return

    # Iniciar sorteio em thread separada
    drawing_thread = threading.Thread(target=player.listen_drawing)
    drawing_thread.start()

    # Aguardar conclusão
    drawing_thread.join()


def test_multiple_players():
    """Teste com múltiplos jogadores"""
    print("\n" + "="*60)
    print("TESTE: Múltiplos Jogadores")
    print("="*60 + "\n")

    # Criar jogo
    creator = BingoPlayer("Criador")
    if not creator.create_game("Teste Multi Player"):
        print("Erro ao criar jogo")
        return

    game_id = creator.game_id

    # Criar jogadores
    players = [
        BingoPlayer("Alice"),
        BingoPlayer("Bob"),
        BingoPlayer("Carol"),
        BingoPlayer("Dave")
    ]

    # Registrar todos os jogadores
    for player in players:
        if not player.register(game_id):
            print(f"Erro ao registrar {player.player_name}")
            return

    # Iniciar sorteio para todos em threads separadas
    threads = []
    for player in players:
        thread = threading.Thread(target=player.listen_drawing)
        thread.start()
        threads.append(thread)

    # Aguardar todas as threads
    for thread in threads:
        thread.join()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == 'single':
            test_single_player()
        elif sys.argv[1] == 'multi':
            test_multiple_players()
        else:
            print("Uso: python test_client.py [single|multi]")
    else:
        print("\nCliente de Teste do Bingo gRPC")
        print("="*60)
        print("\nModos disponíveis:")
        print("  python test_client.py single    - Teste com 1 jogador")
        print("  python test_client.py multi     - Teste com 4 jogadores")
        print("="*60 + "\n")

