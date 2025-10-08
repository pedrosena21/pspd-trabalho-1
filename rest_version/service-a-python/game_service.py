# FastAPI REST/JSON version of the gRPC GameService you shared
# -----------------------------------------------------------
# This exposes JSON endpoints that mirror the CreateGame, RegisterPlayer,
# DrawNumber, MarkNumber, and CheckBingo RPCs.
#
# It also demonstrates calling a *REST* ValidationService running at
# http://localhost:50052 with the following assumed endpoints:
#   POST /register-card {"player_id": str, "card_numbers": [int]}
#   POST /validate-number {"player_id": str, "number": int} -> {"success": bool}
#   POST /validate-bingo {"player_id": str, "numbers": [int]} -> {"bingo": bool}
# If your ValidationService is still gRPC-only, see the GRPCClient stub at the
# bottom for how to swap to gRPC calls instead.
#
# --- How to run ---
# 1) pip install fastapi uvicorn httpx
# 2) uvicorn game_service_rest:app --host 0.0.0.0 --port 50051 --reload
#
# --- Example requests ---
# Create a game:
# curl -s -X POST http://localhost:50051/games -H 'Content-Type: application/json' \
#   -d '{"game_name":"Noite do Bingo"}'
# -> {"game_id":"..."}
#
# Register a player:
# curl -s -X POST http://localhost:50051/games/<game_id>/players -H 'Content-Type: application/json' \
#   -d '{"player_name":"Ana"}'
# -> {"player_id":"...","card_numbers":[...],"success":true}
#
# Draw a number:
# curl -s -X POST http://localhost:50051/games/<game_id>/draw
# -> {"number":42,"success":true}
#
# Mark a number:
# curl -s -X POST http://localhost:50051/players/<player_id>/mark -H 'Content-Type: application/json' \
#   -d '{"number":42}'
# -> {"success":true}
#
# Check bingo:
# curl -s "http://localhost:50051/games/<game_id>/bingo?player_id=<player_id>"
# -> {"bingo":false}

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Tuple
import uuid
import random
import httpx

# -----------------------------
# Domain model (same semantics)
# -----------------------------

class Game:
    def __init__(self, game_id: str, game_name: str):
        self.game_id = game_id
        self.game_name = game_name
        self.players: Dict[str, Dict[str, object]] = {}
        self.drawn_numbers: List[int] = []

    def register_player(self, player_name: str) -> Tuple[str, List[int]]:
        player_id = str(uuid.uuid4())
        # 24 unique numbers between 1 and 75 (like your original code)
        card = random.sample(range(1, 76), 24)
        self.players[player_id] = {"name": player_name, "card": card}
        return player_id, card

# -----------------------------
# Validation service (REST client)
# -----------------------------

class ValidationRESTClient:
    def __init__(self, base_url: str = "http://localhost:50052"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=5.0)

    def register_card(self, player_id: str, card_numbers: List[int]) -> None:
        try:
            resp = self.client.post(
                f"{self.base_url}/register-card",
                json={"player_id": player_id, "card_numbers": card_numbers},
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            print(f"[GAME SERVICE] Erro ao registrar cartela no ValidationService (REST): {e}")

    def validate_number(self, player_id: str, number: int) -> bool:
        try:
            resp = self.client.post(
                f"{self.base_url}/validate-number",
                json={"player_id": player_id, "number": number},
            )
            resp.raise_for_status()
            data = resp.json()
            return bool(data.get("success", False))
        except httpx.HTTPError as e:
            print(f"[GAME SERVICE] Erro ao validar número (REST): {e}")
            return False

    def validate_bingo(self, player_id: str, numbers: List[int]) -> bool:
        try:
            resp = self.client.post(
                f"{self.base_url}/validate-bingo",
                json={"player_id": player_id, "numbers": numbers},
            )
            resp.raise_for_status()
            data = resp.json()
            return bool(data.get("bingo", False))
        except httpx.HTTPError as e:
            print(f"[GAME SERVICE] Erro ao verificar bingo (REST): {e}")
            return False

# -----------------------------
# FastAPI app & schemas
# -----------------------------

app = FastAPI(title="Game Service (REST)")

# In-memory state (like your gRPC server)
games: Dict[str, Game] = {}
# Optional reverse index to find which game a player is in
player_to_game: Dict[str, str] = {}

# Choose which Validation client to use
validation_client = ValidationRESTClient(base_url="http://localhost:50052")
# To use gRPC instead, uncomment below and comment out the REST client above:
# validation_client = ValidationGRPCClient()

class CreateGameRequest(BaseModel):
    game_name: str = Field(..., description="Nome do jogo")

class CreateGameResponse(BaseModel):
    game_id: str

class RegisterPlayerRequest(BaseModel):
    player_name: str

class RegisterPlayerResponse(BaseModel):
    player_id: Optional[str] = None
    card_numbers: Optional[List[int]] = None
    success: bool

class DrawNumberResponse(BaseModel):
    number: Optional[int] = None
    success: bool

class MarkNumberRequest(BaseModel):
    number: int

class MarkNumberResponse(BaseModel):
    success: bool

class CheckBingoResponse(BaseModel):
    bingo: bool

# -----------------------------
# Endpoints mapping 1:1 to RPCs
# -----------------------------

@app.post("/games", response_model=CreateGameResponse)
def create_game(payload: CreateGameRequest):
    game_id = str(uuid.uuid4())
    games[game_id] = Game(game_id, payload.game_name)
    print(f"[GAME SERVICE] Jogo criado: {payload.game_name} ({game_id})")
    return CreateGameResponse(game_id=game_id)

@app.post("/games/{game_id}/players", response_model=RegisterPlayerResponse)
def register_player(game_id: str, payload: RegisterPlayerRequest):
    if game_id not in games:
        return RegisterPlayerResponse(success=False)

    game = games[game_id]
    player_id, card = game.register_player(payload.player_name)
    player_to_game[player_id] = game_id

    print(f"[GAME SERVICE] Jogador registrado: {payload.player_name} ({player_id})")
    print(f"  Cartela: {card}")

    # Notify ValidationService
    validation_client.register_card(player_id=player_id, card_numbers=card)
    print(f"[GAME SERVICE] Cartela registrada no ValidationService para {player_id}")

    return RegisterPlayerResponse(player_id=player_id, card_numbers=card, success=True)

@app.post("/games/{game_id}/draw", response_model=DrawNumberResponse)
def draw_number(game_id: str):
    if game_id not in games:
        return DrawNumberResponse(success=False)

    game = games[game_id]
    number = random.randint(1, 75)
    while number in game.drawn_numbers:
        number = random.randint(1, 75)
    game.drawn_numbers.append(number)

    print(f"[GAME SERVICE] Número sorteado: {number}")
    return DrawNumberResponse(number=number, success=True)

@app.post("/players/{player_id}/mark", response_model=MarkNumberResponse)
def mark_number(player_id: str, payload: MarkNumberRequest):
    # Validate via ValidationService
    ok = validation_client.validate_number(player_id=player_id, number=payload.number)
    if ok:
        print(f"[GAME SERVICE] Número {payload.number} marcado para {player_id}")
    else:
        print(f"[GAME SERVICE] Número {payload.number} NÃO encontrado para {player_id}")
    return MarkNumberResponse(success=ok)

@app.get("/games/{game_id}/bingo", response_model=CheckBingoResponse)
def check_bingo(game_id: str, player_id: str):
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")

    game = games[game_id]
    bingo = validation_client.validate_bingo(player_id=player_id, numbers=game.drawn_numbers)
    print(f"[GAME SERVICE] Bingo verificado para {player_id}: {bingo}")
    return CheckBingoResponse(bingo=bingo)

# -----------------------------
# Health endpoint (useful in tests)
# -----------------------------

@app.get("/healthz")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.getenv("PORT", "50051"))
    uvicorn.run(app, host="0.0.0.0", port=port)
