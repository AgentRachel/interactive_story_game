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

# Serve frontend files
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

# Root redirect to frontend
@app.get("/")
async def root():
    from fastapi.responses import FileResponse
    return FileResponse("frontend/index.html")

# Start AI event loop on startup
@app.on_event("startup")
async def startup_event():
    # Enable AI events
    asyncio.create_task(engine.trigger_ai_events())
    print("[STARTUP] AI event generation enabled")

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
    await websocket.accept()
    print(f"[ENDPOINT] WebSocket accepted for {player_id}")

    # Detect optional room/room_code from query params (for story sessions)
    params = websocket.query_params
    room_code = params.get("room") or params.get("room_code")

    # Create player (pass room_code if present)
    player = engine.setup_player(websocket, player_id, room_code=room_code)
    print(f"[ENDPOINT] Player created: {player.name}")

    # include total players and player index in welcome for proper client numbering
    player_list = list(engine.players.keys())
    player_index = player_list.index(player.player_id) + 1 if player.player_id in player_list else 1
    welcome_msg = {
        "type": "welcome",
        "message": f"Welcome {player_id}!",
        "mode": engine.mode,
        "difficulty": engine.difficulty,
        "player": player.to_dict(),
        "total_players": len(engine.players),
        "player_index": player_index,
        "room_code": room_code
    }
    await websocket.send_json(welcome_msg)
    print(f"[ENDPOINT] Welcome sent to {player_id} (index {player_index})")
    
    # Keep connection alive and listen for messages
    try:
        while True:
            data = await websocket.receive_json()
            print(f"[ENDPOINT] {player_id} action: {data.get('type')}")
            await engine.handle_action(player, data)
    except Exception as e:
        print(f"[ENDPOINT] {player_id} disconnected: {type(e).__name__}")
    finally:
        if player.player_id in engine.players:
            del engine.players[player.player_id]
        print(f"[ENDPOINT] {player_id} cleanup complete")

# Additional Game Endpoints

@app.post("/game/add-ai-players")
async def add_ai_players(count: int = Query(1)):
    """Add AI players to the game (for Game Mode)"""
    added = []
    for i in range(count):
        ai_name = f"AI_Player_{len(engine.players) + i + 1}"
        engine.add_ai_player(ai_name)
        added.append(ai_name)
    return {"added": added, "total_players": len(engine.players)}

@app.post("/game/inject-event")
async def inject_event(event_type: str = Query("ai_event"), room: str = Query("Hallway"), message: str = Query("")):
    """Inject a custom event into the game (spectator/GM feature)"""
    event = {
        "type": event_type,
        "room": room,
        "text": message or f"A {event_type} occurred in {room}!",
        "timestamp": asyncio.get_event_loop().time()
    }
    engine.event_engine.add_event(event)
    await engine.broadcast_room_events(room)
    return {"event": event, "status": "injected"}

@app.get("/game/event-log")
async def get_event_log(limit: int = Query(100)):
    """Get the event log (for display/export)"""
    from backend.utils import export_event_log
    events = engine.event_engine.events[-limit:]
    return {
        "total_events": len(engine.event_engine.events),
        "returned": len(events),
        "events": events
    }

@app.post("/game/export-log")
async def export_log(format: str = Query("json")):
    """Export event log in different formats"""
    from backend.utils import export_event_log
    exported = export_event_log(engine.event_engine.events, format=format)
    return {
        "format": format,
        "content": exported,
        "timestamp": asyncio.get_event_loop().time()
    }

@app.get("/game/export-pdf")
async def export_pdf():
    """Export current game session as PDF"""
    try:
        from backend.utils import generate_story_pdf
        
        session_data = {
            "mode": engine.mode,
            "difficulty": engine.difficulty,
            "players": [p.to_dict() for p in engine.players.values()],
            "events": engine.event_engine.events,
            "rooms": list(engine.rooms.keys())
        }
        
        pdf_bytes = generate_story_pdf(session_data)
        
        from fastapi.responses import Response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=game_session.pdf"}
        )
    except ImportError:
        return {"error": "PDF export requires weasyprint. Install with: pip install weasyprint"}
    except Exception as e:
        return {"error": f"PDF generation failed: {str(e)}"}

@app.post("/game/save-session")
async def save_session(session_name: str = Query("autosave")):
    """Save the current game session"""
    from backend.db import Database
    
    session_data = {
        "name": session_name,
        "mode": engine.mode,
        "difficulty": engine.difficulty,
        "players": [p.to_dict() for p in engine.players.values()],
        "events": engine.event_engine.events
    }
    
    db = Database()
    db.save_session(session_data)
    
    return {
        "status": "saved",
        "session": session_name,
        "timestamp": asyncio.get_event_loop().time()
    }

@app.get("/game/sessions")
async def list_sessions():
    """List all saved game sessions"""
    from backend.db import Database
    
    db = Database()
    sessions = db.load_sessions()
    
    return {
        "total": len(sessions),
        "sessions": sessions
    }


@app.post("/story/new")
async def create_story(world: str = Query("default"), character: str = Query("Player"), genre: str = Query("mystery"), advanced: str = Query("")):
    """Create a new story session and return a room code"""
    import random, string
    from backend.db import Database

    room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    session = {
        "room_code": room_code,
        "world": world,
        "character": character,
        "genre": genre,
        "advanced": advanced,
        "created_at": asyncio.get_event_loop().time()
    }
    db = Database()
    sessions = db.load_sessions()
    sessions[room_code] = session
    db._write_json(db.sessions_file, sessions)

    return {"room_code": room_code, "session": session}


@app.get("/story/list")
async def list_stories():
    from backend.db import Database
    db = Database()
    sessions = db.load_sessions()
    return {"total": len(sessions), "sessions": sessions}


# Duplicate API under /api/story/* in case routing or proxies expect /api prefix
@app.post("/api/story/new")
async def api_create_story(world: str = Query("default"), character: str = Query("Player"), genre: str = Query("mystery"), advanced: str = Query("")):
    import random, string
    from backend.db import Database

    room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    session = {
        "room_code": room_code,
        "world": world,
        "character": character,
        "genre": genre,
        "advanced": advanced,
        "created_at": asyncio.get_event_loop().time()
    }
    db = Database()
    sessions = db.load_sessions()
    sessions[room_code] = session
    db._write_json(db.sessions_file, sessions)

    return {"room_code": room_code, "session": session}


@app.get("/api/story/list")
async def api_list_stories():
    from backend.db import Database
    db = Database()
    sessions = db.load_sessions()
    return {"total": len(sessions), "sessions": sessions}

