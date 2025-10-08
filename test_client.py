"""
Cliente de teste CORRIGIDO para o sistema de Bingo gRPC
Usa os endpoints corretos do stub Node.js
"""

import requests
import time
import threading
import json


class BingoPlayer:
    def __init__(self, player_name, stub_url='http://bingo-api:80'):
        self.player_name = player_name
        self.stub_url = stub_url

        self.player_id = None
        self.card = []
        self.marked = set()
        self.game_id = None

        # Sessão HTTP persistente
        self.session = requests.Session()

    def create_game(self, game_name="Bingo Test"):
        """Cria um novo jogo"""
        try:
            response = self.session.post(
                f"{self.stub_url}/create-game",  # ✅ Endpoint correto
                json={"game_name": game_name},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('game_id'):
                    self.game_id = data['game_id']
                    print(f"✓ Jogo criado: {self.game_id}")
                    return True

            print("✗ Erro: não foi possível criar o jogo")
            print(f"   Resposta: {response.text}")
            return False

        except requests.exceptions.RequestException as e:
            print(f"✗ Erro de conexão ao criar jogo: {e}")
            return False

    def register(self, game_id):
        """Registra o jogador no jogo"""
        self.game_id = game_id

        try:
            response = self.session.post(
                f"{self.stub_url}/register-player",  # ✅ Endpoint correto
                json={
                    "game_id": game_id,
                    "player_name": self.player_name
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.player_id = data['player_id']
                    self.card = data['card_numbers']  # ✅ Nome correto do campo
                    print(f"\n{'='*60}")
                    print(f"Jogador: {self.player_name}")
                    print(f"ID: {self.player_id}")
                    print(f"Cartela: {self.card}")
                    print(f"{'='*60}\n")
                    return True

            print(f"✗ Erro ao registrar {self.player_name}")
            print(f"   Resposta: {response.text}")
            return False

        except requests.exceptions.RequestException as e:
            print(f"✗ Erro de conexão ao registrar: {e}")
            return False

    def listen_drawing(self):
        """Escuta o sorteio de números (em thread separada)"""
        max_retries = 3
        retry_count = 0

        try:
            while True:
                try:
                    # Sorteia um número
                    response = self.session.post(
                        f"{self.stub_url}/draw-number",  # ✅ Endpoint correto
                        json={"game_id": self.game_id},
                        timeout=60
                    )

                    retry_count = 0  # Reset contador em caso de sucesso

                    if response.status_code != 200:
                        print(f"Erro HTTP: {response.status_code}")
                        break

                    data = response.json()
                    if not data.get('success'):
                        print("Sorteio retornou success=false, encerrando...")
                        break

                    number = data['number']
                    print(f"\n🎲 NÚMERO SORTEADO: {number}")

                    time.sleep(0.5)  # Delay após receber número

                    # Verifica se tem o número na cartela
                    if number in self.card and number not in self.marked:
                        self.mark_number(number)

                        time.sleep(0.5)  # Delay após marcar

                        # Verifica se completou o bingo
                        if len(self.marked) == len(self.card):
                            time.sleep(1)
                            self.declare_bingo()
                            break

                    time.sleep(2.5)  # Delay maior entre sorteios

                except requests.exceptions.ConnectionError as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        print(f"\nErro de conexão após {max_retries} tentativas: {e}")
                        break
                    print(f"\nErro de conexão, tentando novamente ({retry_count}/{max_retries})...")
                    time.sleep(3)

        except requests.exceptions.RequestException as e:
            print(f"Erro no sorteio: {e}")
        except KeyboardInterrupt:
            print("\nSorteio interrompido pelo usuário")

    def mark_number(self, number):
        """Marca um número na cartela"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    f"{self.stub_url}/mark-number",  # ✅ Endpoint correto
                    json={
                        "game_id": self.game_id,
                        "player_id": self.player_id,
                        "number": number
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        self.marked.add(number)
                        print(f"  ✓ {self.player_name} marcou o número {number} ({len(self.marked)}/{len(self.card)})")
                    else:
                        print(f"  ✗ Número {number} inválido ou não está na cartela")
                    return

            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    print(f"  Tentando reconectar ({attempt + 1}/{max_retries})...")
                    time.sleep(2)
                    continue
                else:
                    print(f"✗ Erro ao marcar número após {max_retries} tentativas")
            except requests.exceptions.RequestException as e:
                print(f"✗ Erro ao marcar número: {e}")
                return

    def declare_bingo(self):
        """Declara BINGO"""
        print(f"\n{'='*60}")
        print(f"🎉 {self.player_name} está declarando BINGO!")
        print(f"{'='*60}")

        try:
            response = self.session.post(
                f"{self.stub_url}/check-bingo",  # ✅ Endpoint correto
                json={
                    "game_id": self.game_id,
                    "player_id": self.player_id
                },
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('bingo'):
                    print(f"\n🏆 VITÓRIA! Bingo confirmado.")
                else:
                    print(f"\n❌ Bingo inválido.")

        except requests.exceptions.RequestException as e:
            print(f"✗ Erro ao verificar bingo: {e}")

    def get_card(self):
        """Obtém a cartela do jogador"""
        try:
            response = self.session.post(  # ✅ Mudou para POST
                f"{self.stub_url}/get-card",
                json={"player_id": self.player_id},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('card_numbers', [])

            return []

        except requests.exceptions.RequestException as e:
            print(f"✗ Erro ao obter cartela: {e}")
            return []


def test_connection(stub_url='http://bingo-api:80'):
    """Testa a conexão com o stub"""
    print("\n🔍 Testando conexão com o stub Node.js...")

    urls_to_try = [
        stub_url,
        'http://bingo-api',
        'http://localhost:8080'
    ]

    for url in urls_to_try:
        try:
            print(f"Tentando: {url}")
            session = requests.Session()
            response = session.get(f"{url}/docs", timeout=3)
            if response.status_code == 200:
                print(f"✓ Swagger acessível em {url}/docs!\n")
                return url
        except requests.exceptions.RequestException:
            continue

    print(f"✗ Não foi possível conectar ao stub")
    print(f"   Certifique-se de que o stub Node.js está rodando\n")
    return None


def test_single_player():
    """Teste com um único jogador"""
    print("\n" + "="*60)
    print("TESTE: Jogador Único")
    print("="*60 + "\n")

    stub_url = test_connection()
    if not stub_url:
        return

    player = BingoPlayer("Alice", stub_url)

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

    stub_url = test_connection()
    if not stub_url:
        return

    # Criar jogo
    creator = BingoPlayer("Criador", stub_url)
    if not creator.create_game("Teste Multi Player"):
        print("Erro ao criar jogo")
        return

    game_id = creator.game_id

    # Criar jogadores
    players = [
        BingoPlayer("Alice", stub_url),
        BingoPlayer("Bob", stub_url),
        BingoPlayer("Carol", stub_url),
        BingoPlayer("Dave", stub_url)
    ]

    # Registrar todos os jogadores
    for player in players:
        if not player.register(game_id):
            print(f"Erro ao registrar {player.player_name}")
            return
        time.sleep(0.2)  # Pequeno delay entre registros

    # Iniciar sorteio para todos em threads separadas
    threads = []
    for player in players:
        thread = threading.Thread(target=player.listen_drawing)
        thread.start()
        threads.append(thread)

    # Aguardar todas as threads
    for thread in threads:
        thread.join()


def test_api_endpoints():
    """Teste rápido dos endpoints da API"""
    print("\n" + "="*60)
    print("TESTE: Endpoints da API REST")
    print("="*60 + "\n")

    stub_url = test_connection()
    if not stub_url:
        return

    session = requests.Session()

    # 1. Criar jogo
    print("1️⃣  Criando jogo...")
    response = session.post(f"{stub_url}/create-game",
                            json={"game_name": "Teste API"})
    game_data = response.json()
    print(f"   Resposta: {game_data}")

    if not game_data.get('game_id'):
        print("   ✗ Falhou ao criar jogo")
        return

    game_id = game_data['game_id']
    print(f"   ✓ Game ID: {game_id}\n")

    # 2. Registrar jogador
    print("2️⃣  Registrando jogador...")
    response = session.post(f"{stub_url}/register-player",
                            json={"game_id": game_id, "player_name": "TestPlayer"})
    player_data = response.json()
    print(f"   Player ID: {player_data.get('player_id')}")
    print(f"   Cartela: {player_data.get('card_numbers', [])[:10]}... (primeiros 10)")
    print(f"   ✓ Sucesso: {player_data.get('success')}\n")

    player_id = player_data['player_id']
    card = player_data['card_numbers']

    # 3. Sortear número
    print("3️⃣  Sorteando número...")
    response = session.post(f"{stub_url}/draw-number",
                            json={"game_id": game_id})
    draw_data = response.json()
    print(f"   Número sorteado: {draw_data.get('number')}")
    print(f"   ✓ Sucesso: {draw_data.get('success')}\n")

    number = draw_data['number']

    # 4. Marcar número (se estiver na cartela)
    print("4️⃣  Marcando número...")
    response = session.post(f"{stub_url}/mark-number",
                            json={"game_id": game_id, "player_id": player_id, "number": number})
    mark_data = response.json()
    print(f"   Número {number} está na cartela: {number in card}")
    print(f"   ✓ Marcado: {mark_data.get('success')}\n")

    # 5. Obter cartela
    print("5️⃣  Obtendo cartela do jogador...")
    response = session.post(f"{stub_url}/get-card",
                            json={"player_id": player_id})
    card_data = response.json()
    print(f"   Cartela: {card_data.get('card_numbers', [])[:10]}... (primeiros 10)")
    print(f"   ✓ Total de números: {len(card_data.get('card_numbers', []))}\n")

    # 6. Verificar bingo (vai falhar pois não completou)
    print("6️⃣  Verificando BINGO (deve falhar)...")
    response = session.post(f"{stub_url}/check-bingo",
                            json={"game_id": game_id, "player_id": player_id})
    bingo_data = response.json()
    print(f"   BINGO válido: {bingo_data.get('bingo')}")
    print(f"   ✓ Esperado: False (ainda não completou)\n")

    print("="*60)
    print("✓ Teste de API concluído com sucesso!")
    print("="*60 + "\n")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == 'single':
            test_single_player()
        elif sys.argv[1] == 'multi':
            test_multiple_players()
        elif sys.argv[1] == 'api':
            test_api_endpoints()
        else:
            print("Uso: python test_client.py [single|multi|api]")
    else:
        print("\nCliente de Teste do Bingo gRPC via Stub Node.js")
        print("="*60)
        print("\nModos disponíveis:")
        print("  python test_client.py single    - Teste com 1 jogador")
        print("  python test_client.py multi     - Teste com 4 jogadores")
        print("  python test_client.py api       - Teste dos endpoints REST")
        print("\nPré-requisitos:")
        print("  1. ValidationService rodando na porta 50052")
        print("  2. GameService rodando na porta 50051")
        print("  3. Stub Node.js rodando e acessível")
        print("="*60 + "\n")
