import time
import json

class EventEngine:
    def __init__(self, map_obj):
        self.map = map_obj
        self.events = []  # Event queue
        self.max_events = 1000  # Keep last 1000 events
        
    def add_event(self, event):
        """Add event with timestamp"""
        event["timestamp"] = time.time()
        self.events.append(event)
        
        # Keep event buffer bounded
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]

    def process_action(self, player, action):
        """Process player action and create events"""
        action_type = action.get("type")
        
        if action_type == "move":
            room_name = action.get("room")
            if player.move_to(room_name):
                self.add_event({
                    "type": "move",
                    "player": player.name,
                    "room": player.get_room_name(),
                    "visibility": "room"  # Only visible to players in room
                })
        
        elif action_type == "chat":
            message = action.get("message", "")
            whisper = action.get("whisper", False)
            
            self.add_event({
                "type": "chat" if not whisper else "whisper",
                "player": player.name,
                "message": message,
                "room": player.get_room_name(),
                "visibility": "whisper" if whisper else "room"
            })

    def filter_events_for_player(self, player):
        """Filter events visible to player based on awareness and location"""
        filtered = []
        player_room = player.get_room_name()
        
        for event in self.events[-100:]:  # Last 100 events
            visibility = event.get("visibility", "global")
            event_room = event.get("room", "")
            
            if visibility == "global":
                filtered.append(event)
            elif visibility == "room" and event_room == player_room:
                filtered.append(event)
            elif visibility == "whisper" and event.get("player") == player.name:
                filtered.append(event)
            elif event.get("type") == "ai_event":
                # AI events visible based on sound propagation (awareness)
                if event_room == player_room or player.can_hear_event(event_room, event.get("volume", 1)):
                    filtered.append(event)
        
        return filtered

    def get_events_for_room(self, room_name):
        """Get all recent events for a specific room"""
        return [e for e in self.events[-50:] if e.get("room") == room_name]
    
    def get_events_for_player(self, player):
        """Wrapper for filter_events_for_player"""
        return self.filter_events_for_player(player)
