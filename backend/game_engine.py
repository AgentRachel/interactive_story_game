import asyncio
import json
import random
from backend.players import Player
from backend.maps import MapGenerator
from backend.events import EventEngine
from backend.ai_module import AIEngine
from backend.utils import ROLES, ABILITIES

class GameEngine:
    def __init__(self):
        self.players = {}
        self.map = MapGenerator().generate_default_map()
        self.event_engine = EventEngine(self.map)
        self.ai_engine = AIEngine()
        self.rooms = self.map.rooms
        self.mode = "game"  # "story" or "game"
        self.difficulty = "normal"  # "easy", "normal", "hard"
        self.max_players = 8
        self.ai_slots = 0
        self.started = False
        self.events_log = []
        
    def set_game_mode(self, mode, difficulty="normal", ai_slots=0):
        """Set game mode: 'story' (1 player) or 'game' (2-8 players)"""
        self.mode = mode
        self.difficulty = difficulty
        self.ai_slots = ai_slots
        
        if mode == "story":
            self.max_players = 1
        elif mode == "game":
            self.max_players = 8

    async def connect_player(self, websocket, player_id):
        """Handle new player connection"""
        print(f"\n[CONNECT] {player_id} attempting connection...")
        try:
            player = Player(player_id, websocket, self.map)
            self.players[player_id] = player
            await websocket.accept()
            print(f"[CONNECT] {player_id} accepted")
            
            # Send welcome and player state
            welcome_msg = {
                "type": "welcome",
                "message": f"Welcome {player_id}!",
                "mode": self.mode,
                "difficulty": self.difficulty,
                "player": player.to_dict()
            }
            print(f"[CONNECT] {player_id} sending welcome: {welcome_msg}")
            await websocket.send_json(welcome_msg)
            print(f"[CONNECT] {player_id} welcome sent")
            
            # Start listening for this player
            asyncio.create_task(self.listen_player(player))
            print(f"[CONNECT] {player_id} listen task started")
        except Exception as e:
            print(f"[CONNECT] {player_id} error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    def setup_player(self, websocket, player_id, room_code=None):
        """Setup a player without accepting websocket (endpoint handles accept).
        Optionally associate the player with a story room_code."""
        player = Player(player_id, websocket, self.map)
        if room_code:
            player.room_code = room_code
        self.players[player_id] = player
        print(f"[SETUP] Player {player_id} created, room: {player.current_room}, room_code: {room_code}")
        return player

    async def listen_player(self, player):
        """Listen for player actions"""
        try:
            print(f"[LISTEN] Starting for {player.name}")
            while True:
                data = await player.websocket.receive_json()
                print(f"[LISTEN] {player.name} received: {data.get('type')}")
                await self.handle_action(player, data)
        except Exception as e:
            print(f"[LISTEN] {player.name} error: {type(e).__name__}")
        finally:
            if player.player_id in self.players:
                del self.players[player.player_id]
            print(f"[LISTEN] {player.name} stopped")

    async def handle_action(self, player, data):
        """Process player action"""
        action_type = data.get("type")
        print(f"[ACTION] {player.name}: {action_type}")
        
        try:
            if action_type == "move":
                room_name = data.get("room")
                print(f"[ACTION] {player.name} moving to {room_name}")
                if player.move_to(room_name):
                    event = {
                        "type": "player_moved",
                        "player": player.name,
                        "room": player.get_room_name()
                    }
                    self.event_engine.add_event(event)
                    await self.broadcast_room_events(player.get_room_name())
                    print(f"[ACTION] {player.name} moved successfully")
                else:
                    print(f"[ACTION] {player.name} move failed - not connected")
                    
            elif action_type == "chat":
                message = data.get("message", "")
                whisper = data.get("whisper", False)
                target = data.get("target", None)
                print(f"[ACTION] {player.name} chat: {message[:30]}...")
                
                chat_event = {
                    "type": "chat" if not whisper else "whisper",
                    "player": player.name,
                    "message": message,
                    "room": player.get_room_name()
                }
                self.event_engine.add_event(chat_event)
                
                if whisper and target:
                    if target in self.players and self.players[target].get_room_name() == player.get_room_name():
                        try:
                            await self.players[target].websocket.send_json({
                                "type": "chat",
                                "player": player.name,
                                "message": f"*whispers* {message}"
                            })
                        except Exception:
                            pass
                else:
                    await self.broadcast_room_events(player.get_room_name())
                    
            elif action_type == "ability":
                ability_name = data.get("ability")
                target = data.get("target")
                print(f"[ACTION] {player.name} ability: {ability_name}")
                event = {
                    "type": "ability_used",
                    "player": player.name,
                    "ability": ability_name,
                    "target": target,
                    "room": player.get_room_name()
                }
                self.event_engine.add_event(event)
                await self.broadcast_room_events(player.get_room_name())
            else:
                print(f"[ACTION] Unknown action type: {action_type}")
        except Exception as e:
            print(f"[ACTION] Error handling {action_type} for {player.name}: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    async def broadcast(self, message, exclude=None):
        """Send message to all connected players"""
        for player_id, player in list(self.players.items()):
            if exclude and player_id == exclude:
                continue
            try:
                await player.websocket.send_json(message)
            except Exception as e:
                print(f"[BROADCAST] Error to {player.name}: {type(e).__name__}")
                if player_id in self.players:
                    del self.players[player_id]

    async def broadcast_room_events(self, room_name):
        """Send room-specific events to players in that room"""
        for player_id, player in list(self.players.items()):
            try:
                if player.get_room_name() == room_name:
                    filtered = self.event_engine.filter_events_for_player(player)
                    if filtered:
                        await player.websocket.send_json({
                            "type": "events",
                            "events": filtered
                        })
            except Exception as e:
                print(f"[BROADCAST_ROOM] Error to {player.name}: {type(e).__name__}")
                if player_id in self.players:
                    del self.players[player_id]

    async def trigger_ai_events(self):
        """Periodically trigger AI events"""
        while True:
            try:
                await asyncio.sleep(10)  # AI event every 10 seconds
                print("[AI] trigger_ai_events loop awake")
                if len(self.players) > 0:
                    ai_events = self.ai_engine.generate_events(self.players, self.map, self.difficulty)
                    print(f"[AI] Generated {len(ai_events)} event(s)")
                    for event in ai_events:
                        self.event_engine.add_event(event)
                        room = event.get("room")
                        if room:
                            await self.broadcast_room_events(room)
                
                # Also control AI players
                await self.control_ai_players()
            except Exception as e:
                print(f"Error generating AI events: {e}")
                await asyncio.sleep(1)  # Don't loop too fast on error
    
    async def control_ai_players(self):
        """Control AI players' actions (movement, chat, etc)"""
        ai_players = [p for p in self.players.values() if hasattr(p, 'is_ai') and p.is_ai]
        
        for ai_player in ai_players:
            actions = self.get_ai_actions(ai_player)
            for action in actions:
                await self.handle_action(ai_player, action)
    
    def assign_roles(self):
        """Assign roles to players in Game Mode"""
        if self.mode != "game":
            return
        
        player_list = list(self.players.values())
        for i, player in enumerate(player_list):
            role = ROLES[i % len(ROLES)]
            player.role = role["name"]
            player.personal_objective = role["objective"]
            player.abilities = role["abilities"].copy()
    
    def add_ai_player(self, name):
        """Add an AI player (simulated player without WebSocket)"""
        from backend.players import Player
        
        # Create a fake websocket-like object for AI players
        class FakeWebSocket:
            async def send_json(self, data):
                pass  # AI players don't need to receive messages
            async def receive_json(self):
                return {}
        
        player = Player(name, FakeWebSocket(), self.map)
        player.is_ai = True
        self.players[name] = player
        print(f"[AI] Added AI player: {name} in {player.current_room}")
        return player

    def get_ai_actions(self, player):
        """Generate random AI player actions"""
        actions = []
        
        # 30% chance to move
        if random.random() < 0.3:
            connected = list(self.map.rooms[player.current_room].connections) if hasattr(self.map.rooms[player.current_room], 'connections') else []
            if connected:
                room_names = [r.name if hasattr(r, 'name') else str(r) for r in connected]
                room = random.choice(room_names)
                actions.append({"type": "move", "room": room})
        
        # 20% chance to chat
        if random.random() < 0.2:
            chats = [
                "I'm looking for something...",
                "Did you see that?",
                "It's quiet here...",
                "What's going on?",
                "I sense something nearby..."
            ]
            actions.append({"type": "chat", "message": random.choice(chats)})
        
        return actions
