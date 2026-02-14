import asyncio
import json
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
        try:
            player = Player(player_id, websocket, self.map)
            self.players[player_id] = player
            await websocket.accept()
            
            # Send welcome and player state
            await websocket.send_json({
                "type": "welcome",
                "message": f"Welcome {player_id}!",
                "mode": self.mode,
                "difficulty": self.difficulty,
                "player": player.to_dict()
            })
            
            # Broadcast new player to others
            await self.broadcast({
                "type": "player_joined",
                "player": player.to_dict(),
                "total_players": len(self.players)
            }, exclude=player_id)
            
            # Start listening for this player
            asyncio.create_task(self.listen_player(player))
        except Exception as e:
            print(f"Error connecting player: {e}")

    async def listen_player(self, player):
        """Listen for player actions"""
        ws = player.websocket
        try:
            while True:
                data = await ws.receive_json()
                await self.handle_action(player, data)
        except Exception as e:
            print(f"Player {player.name} disconnected: {e}")
            if player.player_id in self.players:
                del self.players[player.player_id]
                await self.broadcast({
                    "type": "player_left",
                    "player": player.name,
                    "total_players": len(self.players)
                })

    async def handle_action(self, player, data):
        """Process player action"""
        action_type = data.get("type")
        
        if action_type == "move":
            room_name = data.get("room")
            if player.move_to(room_name):
                event = {
                    "type": "player_moved",
                    "player": player.name,
                    "room": player.get_room_name()
                }
                self.event_engine.add_event(event)
                await self.broadcast_room_events(player.get_room_name())
                
        elif action_type == "chat":
            message = data.get("message", "")
            whisper = data.get("whisper", False)
            target = data.get("target", None)
            
            chat_event = {
                "type": "chat" if not whisper else "whisper",
                "player": player.name,
                "message": message,
                "room": player.get_room_name()
            }
            self.event_engine.add_event(chat_event)
            
            if whisper and target:
                # Send to specific player only if they're in same room
                if target in self.players and self.players[target].get_room_name() == player.get_room_name():
                    await self.players[target].websocket.send_json({
                        "type": "chat",
                        "player": player.name,
                        "message": f"*whispers* {message}"
                    })
            else:
                await self.broadcast_room_events(player.get_room_name())
                
        elif action_type == "ability":
            ability_name = data.get("ability")
            target = data.get("target")
            # Process ability
            event = {
                "type": "ability_used",
                "player": player.name,
                "ability": ability_name,
                "target": target,
                "room": player.get_room_name()
            }
            self.event_engine.add_event(event)
            await self.broadcast_room_events(player.get_room_name())

    async def broadcast(self, message, exclude=None):
        """Send message to all connected players"""
        for player_id, player in self.players.items():
            if exclude and player_id == exclude:
                continue
            try:
                await player.websocket.send_json(message)
            except Exception as e:
                print(f"Error sending to {player_id}: {e}")

    async def broadcast_room_events(self, room_name):
        """Send room-specific events to players in that room"""
        events = self.event_engine.get_events_for_room(room_name)
        for player_id, player in self.players.items():
            if player.get_room_name() == room_name:
                filtered = self.event_engine.filter_events_for_player(player)
                try:
                    await player.websocket.send_json({
                        "type": "events",
                        "events": filtered
                    })
                except Exception as e:
                    print(f"Error sending events to {player_id}: {e}")

    async def trigger_ai_events(self):
        """Periodically trigger AI events"""
        while True:
            await asyncio.sleep(5)  # AI event every 5 seconds
            if len(self.players) > 0:
                ai_events = self.ai_engine.generate_events(self.players, self.map, self.difficulty)
                for event in ai_events:
                    self.event_engine.add_event(event)
                    room = event.get("room")
                    if room:
                        await self.broadcast_room_events(room)
    
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
        """Add an AI player"""
        # This is a placeholder for AI player creation
        pass
