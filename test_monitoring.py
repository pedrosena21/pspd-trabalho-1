import requests
import random
import time
import sys
from concurrent.futures import ThreadPoolExecutor

# Configuração
BASE_URL = "http://localhost:30080"  # Endereço do seu port-forward
NUM_GAMES = 10                       # Quantos jogos simultâneos criar
PLAYERS_PER_GAME = 4                # Jogadores por jogo
DRAW_SPEED = 0.1                    # Segundos entre sorteios (quanto menor, mais rápido gera métricas)

def log(msg):
    print(f"[TESTE] {msg}")

def run_game_simulation(game_index):
    game_name = f"Bingo Load Test {game_index}-{random.randint(1000, 9999)}"

    # 1. Criar Jogo
    try:
        resp = requests.post(f"{BASE_URL}/game/create", json={"game_name": game_name})
        if resp.status_code != 200:
            log(f"Erro ao criar jogo: {resp.text}")
            return

        game_data = resp.json()
        game_id = game_data.get('game_id')
        log(f"🎮 Jogo criado: {game_name} (ID: {game_id})")
    except Exception as e:
        log(f"Erro de conexão: {e}")
        return

    # 2. Registrar Jogadores
    players = []
    for i in range(PLAYERS_PER_GAME):
        p_name = f"Player-{game_index}-{i}"
        try:
            r = requests.post(f"{BASE_URL}/game/register", json={
                "game_id": game_id,
                "player_name": p_name
            })
            if r.status_code == 200:
                p_data = r.json()
                players.append({
                    "id": p_data['player_id'],
                    "name": p_name,
                    "card": p_data.get('card', [])
                })
        except:
            pass

    log(f"👥 {len(players)} jogadores registrados no jogo {game_index}")

    # 3. Loop de Sorteio (Game Loop)
    drawn_numbers = []
    game_over = False

    # Sorteia até 75 números ou alguém ganhar
    for _ in range(75):
        if game_over: break

        # Sorteia número
        try:
            r = requests.post(f"{BASE_URL}/game/draw", json={"game_id": game_id})
            if r.status_code != 200: continue

            data = r.json()
            if not data.get('success'): break

            number = data.get('number')
            drawn_numbers.append(number)
            log(f"🎲 Jogo {game_index}: Sorteado {number}")
        except:
            continue

        # Simula jogadores marcando e conferindo
        for player in players:
            # Tenta marcar (mesmo se não tiver na cartela, gera tráfego de erro/validação)
            try:
                requests.post(f"{BASE_URL}/game/mark", json={
                    "game_id": game_id,
                    "player_id": player['id'],
                    "number": number
                })

                # A cada 5 números sorteados, confere BINGO
                if len(drawn_numbers) % 5 == 0:
                    b_resp = requests.post(f"{BASE_URL}/game/bingo", json={
                        "game_id": game_id,
                        "player_id": player['id']
                    })
                    if b_resp.json().get('bingo'):
                        log(f"🏆 BINGO! O vencedor do jogo {game_index} é {player['name']}!")
                        game_over = True
                        break
            except:
                pass

        time.sleep(DRAW_SPEED)

    log(f"🏁 Jogo {game_index} finalizado.")

def main():
    log("🚀 Iniciando teste de carga...")
    log(f"Config: {NUM_GAMES} jogos, {PLAYERS_PER_GAME} players cada.")

    with ThreadPoolExecutor(max_workers=NUM_GAMES) as executor:
        for i in range(NUM_GAMES):
            executor.submit(run_game_simulation, i+1)

if __name__ == "__main__":
    main()
