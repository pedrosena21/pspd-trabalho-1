# FastAPI REST/JSON version of the gRPC ValidationService
# ------------------------------------------------------
# This mirrors the RPCs: RegisterCard, ValidateNumber, ValidateBingo, GetCard
# and exposes them as simple JSON endpoints expected by the REST GameService.
#
# Endpoints:
#   POST /register-card     -> {"player_id": str, "card_numbers": [int]} -> {"success": bool}
#   POST /validate-number   -> {"player_id": str, "number": int}        -> {"success": bool}
#   POST /validate-bingo    -> {"player_id": str, "numbers": [int]}      -> {"bingo": bool}
#   GET  /card/{player_id}  ->                                              -> {"card_numbers": [int]}
#
# --- How to run ---
# 1) pip install fastapi uvicorn
# 2) uvicorn validation_service_rest:app --host 0.0.0.0 --port 50052 --reload

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict, List, Set

app = FastAPI(title="Validation Service (REST)")

# In-memory storage: player_id -> {"card": List[int], "marked": Set[int]}
players: Dict[str, Dict[str, object]] = {}

# -----------------------------
# Request/Response Schemas
# -----------------------------

class RegisterCardRequest(BaseModel):
    player_id: str = Field(..., description="ID do jogador")
    card_numbers: List[int] = Field(..., description="Cartela com 24 números únicos entre 1 e 75")

class RegisterCardResponse(BaseModel):
    success: bool

class ValidateNumberRequest(BaseModel):
    player_id: str
    number: int

class ValidateNumberResponse(BaseModel):
    success: bool

class ValidateBingoRequest(BaseModel):
    player_id: str
    numbers: List[int]

class ValidateBingoResponse(BaseModel):
    bingo: bool

class GetCardResponse(BaseModel):
    card_numbers: List[int]

# -----------------------------
# Endpoints
# -----------------------------

@app.post("/register-card", response_model=RegisterCardResponse)
def register_card(payload: RegisterCardRequest):
    players[payload.player_id] = {
        "card": list(payload.card_numbers),
        "marked": set(),
    }
    print(f"[VALIDATION SERVICE] Cartela registrada para {payload.player_id}: {payload.card_numbers}")
    return RegisterCardResponse(success=True)

@app.post("/validate-number", response_model=ValidateNumberResponse)
def validate_number(payload: ValidateNumberRequest):
    p = players.get(payload.player_id)
    if p:
        card: List[int] = p["card"]  # type: ignore
        if payload.number in card:
            # ensure we have a set for marked
            if not isinstance(p["marked"], set):
                p["marked"] = set(p["marked"])  # type: ignore
            marked: Set[int] = p["marked"]  # type: ignore
            marked.add(payload.number)
            return ValidateNumberResponse(success=True)
    return ValidateNumberResponse(success=False)

@app.post("/validate-bingo", response_model=ValidateBingoResponse)
def validate_bingo(payload: ValidateBingoRequest):
    p = players.get(payload.player_id)
    if p:
        card_set = set(p["card"])  # type: ignore
        marked_set = set(p["marked"])  # type: ignore
        # Mark any drawn numbers that are on the card (idempotent)
        for n in payload.numbers:
            if n in card_set:
                marked_set.add(n)
        # Persist back (in case marked_set was copied)
        p["marked"] = marked_set
        if card_set.issubset(marked_set):
            return ValidateBingoResponse(bingo=True)
    return ValidateBingoResponse(bingo=False)

@app.get("/card/{player_id}", response_model=GetCardResponse)
def get_card(player_id: str):
    p = players.get(player_id)
    if p:
        return GetCardResponse(card_numbers=list(p["card"]))  # type: ignore
    return GetCardResponse(card_numbers=[])

@app.get("/healthz")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.getenv("PORT", "50052"))
    uvicorn.run(app, host="0.0.0.0", port=port)

