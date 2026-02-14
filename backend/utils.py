# Utility functions and constants for Interactive Story Game

ROLES = [
    {
        "name": "Detective",
        "objective": "Find the hidden culprit",
        "abilities": [
            {"name": "Interrogate", "cooldown": 30},
            {"name": "Investigate", "cooldown": 15}
        ]
    },
    {
        "name": "Suspect",
        "objective": "Avoid being found out",
        "abilities": [
            {"name": "Hide", "cooldown": 20},
            {"name": "Misdirect", "cooldown": 25}
        ]
    },
    {
        "name": "Witness",
        "objective": "Remember the truth",
        "abilities": [
            {"name": "Recall", "cooldown": 10},
            {"name": "Report", "cooldown": 30}
        ]
    },
    {
        "name": "Informant",
        "objective": "Gather secrets",
        "abilities": [
            {"name": "Eavesdrop", "cooldown": 15},
            {"name": "Blackmail", "cooldown": 40}
        ]
    },
]

ABILITIES = {
    "Interrogate": {"duration": 5, "range": "same_room"},
    "Investigate": {"duration": 10, "range": "same_room"},
    "Hide": {"duration": 20, "range": "same_room"},
    "Misdirect": {"duration": 5, "range": "adjacent_room"},
    "Recall": {"duration": 0, "range": "self"},
    "Report": {"duration": 0, "range": "all"},
    "Eavesdrop": {"duration": 10, "range": "adjacent_room"},
    "Blackmail": {"duration": 5, "range": "same_room"},
}

def get_room_adjacency(rooms_dict):
    """Build a map of which rooms are adjacent"""
    adjacency = {}
    for room_name, room in rooms_dict.items():
        adjacency[room_name] = []
        if hasattr(room, "connections"):
            for connected in room.connections:
                if hasattr(connected, "name"):
                    adjacency[room_name].append(connected.name)
    return adjacency

def calculate_sound_propagation(origin_room, target_room, awareness, adjacency):
    """Calculate if sound from origin_room reaches target_room based on awareness"""
    if origin_room == target_room:
        return True
    
    # BFS to find shortest path
    visited = set()
    queue = [(origin_room, 0)]
    
    while queue:
        current, distance = queue.pop(0)
        if current == target_room:
            return distance < awareness
        
        if current in visited:
            continue
        visited.add(current)
        
        for neighbor in adjacency.get(current, []):
            if neighbor not in visited:
                queue.append((neighbor, distance + 1))
    
    return False

def format_player_list(players):
    """Format list of players for display"""
    return [{"name": p.name, "room": p.get_room_name(), "role": p.role} for p in players.values()]

def export_event_log(events, format="json"):
    """Export event log in different formats"""
    if format == "json":
        return "\n".join([str(e) for e in events])
    elif format == "text":
        return "\n".join([f"{e.get('type')}: {e.get('player', 'System')} - {e.get('text', '')}" for e in events])
    return str(events)

