import time
import json

class Player:
    def __init__(self, name, websocket, map_obj):
        self.name = name
        self.websocket = websocket
        self.player_id = name
        # Store room name as string, not object
        self.current_room = list(map_obj.rooms.keys())[0]  # Start in first room (as string)
        self.map = map_obj  # Keep reference to map for room lookups
        self.awareness = 5
        self.focus = "normal"
        self.role = None
        self.personal_objective = None
        self.abilities = []
        self.history = []
        self.is_ai = False
        self.connected_at = time.time()
        self.last_action = time.time()
        
    def move_to(self, room_name):
        """Move player to adjacent room"""
        # Get current room object
        current_room_obj = self.map.rooms.get(self.current_room)
        if not current_room_obj:
            return False
        
        # Check if target is connected to current
        connected_names = [r.name for r in current_room_obj.connections]
        if room_name in connected_names:
            self.current_room = room_name
            self.last_action = time.time()
            return True
        return False

    def get_connected_rooms(self):
        """Get names of connected rooms"""
        current_room_obj = self.map.rooms.get(self.current_room)
        if not current_room_obj:
            return []
        return [r.name for r in current_room_obj.connections]
    
    def get_room_name(self):
        """Get current room name"""
        return self.current_room
    
    def can_hear_event(self, event_room, event_volume=1):
        """Check if player can hear event based on awareness"""
        if self.current_room == event_room:
            return True
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
