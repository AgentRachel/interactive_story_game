import time
import json

class Player:
    def __init__(self, name, websocket, map_obj):
        self.name = name
        self.websocket = websocket
        self.player_id = name  # Unique identifier
        self.current_room = list(map_obj.rooms.keys())[0]  # Start in first room
        self.awareness = 5  # How far sound travels
        self.focus = "normal"  # "normal", "alert", "distracted"
        self.role = None  # Secret role in Game Mode
        self.personal_objective = None
        self.abilities = []  # List of ability dicts: {"name": "...", "cooldown": 0}
        self.history = []  # Chat/event history
        self.is_ai = False
        self.connected_at = time.time()
        self.last_action = time.time()
        
    def move_to(self, room_name):
        """Move player to adjacent room"""
        connected_names = [r.name for r in self.get_connected_rooms()]
        if room_name in connected_names:
            self.current_room = room_name
            self.last_action = time.time()
            return True
        return False

    def get_connected_rooms(self):
        """Get Room objects that are connected to current room"""
        if hasattr(self.current_room, "connections"):
            return self.current_room.connections if isinstance(self.current_room, dict) else []
        return []
    
    def get_room_name(self):
        """Get current room name as string"""
        if isinstance(self.current_room, dict):
            return list(self.current_room.keys())[0] if self.current_room else "Unknown"
        if hasattr(self.current_room, "name"):
            return self.current_room.name
        return str(self.current_room)
    
    def can_hear_event(self, event_room, event_volume=1):
        """Check if player can hear event in another room based on awareness"""
        if self.get_room_name() == event_room:
            return True
        # Sound propagates based on player awareness and event volume
        return event_volume >= self.awareness
    
    def to_dict(self):
        """Serialize player for JSON"""
        return {
            "name": self.name,
            "current_room": self.get_room_name(),
            "role": self.role,
            "abilities": self.abilities,
            "awareness": self.awareness,
            "focus": self.focus,
            "is_ai": self.is_ai
        }
