import random
import time

class AIEngine:
    def __init__(self):
        self.last_event_time = {}
        self.difficulty_settings = {
            "easy": {"frequency": 10, "intensity": 1},
            "normal": {"frequency": 5, "intensity": 2},
            "hard": {"frequency": 2, "intensity": 3}
        }
    
    def generate_events(self, players, map_obj, difficulty="normal"):
        """Generate AI events based on difficulty"""
        messages = []
        settings = self.difficulty_settings.get(difficulty, self.difficulty_settings["normal"])
        
        # Only generate events at the frequency interval
        if random.randint(0, 10) > settings["frequency"]:
            return messages
        
        rooms = list(map_obj.rooms.values())
        
        # Room-specific events
        for _ in range(settings["intensity"]):
            room = random.choice(rooms)
            room_name = room.name if hasattr(room, "name") else str(room)
            
            event_templates = [
                f"A mysterious sound echoes through {room_name}...",
                f"Shadows flicker in {room_name}.",
                f"Something moves in {room_name}!",
                f"You hear footsteps in {room_name}.",
                f"The air grows cold in {room_name}.",
            ]
            
            if difficulty == "hard":
                event_templates.extend([
                    f"DANGER: Something malevolent appears in {room_name}!",
                    f"An alarm triggers in {room_name}!",
                ])
            
            text = random.choice(event_templates)
            
            messages.append({
                "type": "ai_event",
                "room": room_name,
                "text": text,
                "volume": settings["intensity"],  # Sound propagation
                "visibility": "ai_event",
                "timestamp": time.time()
            })
        
        return messages
    
    def generate_narrative_event(self, players, character):
        """Generate story-mode narrative event for a character"""
        templates = [
            f"{character.name} recalls a distant memory...",
            f"{character.name} notices something unusual.",
            f"A stranger approaches {character.name}.",
            f"{character.name}'s past catches up with them...",
        ]
        return random.choice(templates)
