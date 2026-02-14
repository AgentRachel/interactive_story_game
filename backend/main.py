from fastapi import FastAPI, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
from backend.game_engine import GameEngine

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

engine = GameEngine()

# Start AI event loop on startup
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(engine.trigger_ai_events())

@app.get("/health")
async def health_check():
    return {"status": "ok", "players": len(engine.players)}

@app.get("/players")
async def get_players():
    """Get list of connected players"""
    return {
        "players": [p.to_dict() for p in engine.players.values()],
        "count": len(engine.players),
        "mode": engine.mode,
        "difficulty": engine.difficulty
    }

@app.post("/game/mode")
async def set_game_mode(mode: str = Query("game"), difficulty: str = Query("normal"), ai_slots: int = Query(0)):
    """Set game mode (story or game) and difficulty"""
    engine.set_game_mode(mode, difficulty, ai_slots)
    return {
        "mode": mode,
        "difficulty": difficulty,
        "ai_slots": ai_slots
    }

@app.post("/game/assign-roles")
async def assign_roles():
    """Assign roles to all players"""
    engine.assign_roles()
    return {
        "players": [p.to_dict() for p in engine.players.values()]
    }

@app.post("/game/start")
async def start_game():
    """Start the game"""
    engine.started = True
    return {
        "status": "Game started",
        "players": len(engine.players),
        "rooms": list(engine.rooms.keys())
    }

@app.websocket("/ws/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: str):
    await engine.connect_player(websocket, player_id)

