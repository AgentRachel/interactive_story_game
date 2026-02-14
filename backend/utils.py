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

def generate_story_pdf(session_data):
    """Generate a PDF from a game session using weasyprint"""
    try:
        from weasyprint import HTML, CSS
        from io import BytesIO
        import json
        
        # Create HTML content
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; border-bottom: 2px solid #333; }}
                h2 {{ color: #666; margin-top: 20px; }}
                .player {{ background: #f0f0f0; padding: 10px; margin: 5px 0; border-radius: 3px; }}
                .event {{ background: #e8f4f8; padding: 8px; margin: 3px 0; border-left: 3px solid #0099cc; }}
                .summary {{ color: #666; font-size: 12px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <h1>Interactive Story Game Session</h1>
            <div class="summary">
                <p><strong>Mode:</strong> {session_data.get('mode', 'unknown')}</p>
                <p><strong>Difficulty:</strong> {session_data.get('difficulty', 'normal')}</p>
                <p><strong>Total Events:</strong> {len(session_data.get('events', []))}</p>
            </div>
            
            <h2>Players</h2>
            {' '.join([f'<div class="player"><strong>{p.get("name")}</strong> - Role: {p.get("role", "None")} - Room: {p.get("current_room", "Unknown")}</div>' for p in session_data.get('players', [])])}
            
            <h2>Event Log</h2>
            {' '.join([f'<div class="event"><strong>{e.get("type")}</strong>: {e.get("player", "System")} - {e.get("message") or e.get("text") or "event"}</div>' for e in session_data.get('events', [])])}
            
        </body>
        </html>
        """
        
        # Generate PDF
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    
    except ImportError:
        raise ImportError("weasyprint is required for PDF export. Install with: pip install weasyprint")
    except Exception as e:
        raise Exception(f"PDF generation error: {str(e)}")

def generate_narrative_event(player_name, context, difficulty="normal"):
    """Generate a narrative event for story mode"""
    narratives = {
        "easy": [
            f"You hear {player_name} moving around nearby.",
            f"{player_name} appears in the room.",
            f"A gentle breeze carries a whisper from {player_name}.",
            "You sense something is shifting in the environment.",
            "Time seems to move slowly here..."
        ],
        "normal": [
            f"{player_name} suddenly looks your way.",
            f"The atmosphere changes when {player_name} arrives.",
            f"You hear {player_name} whispering something cryptic.",
            "A mysterious figure emerges from the shadows.",
            "The room feels electric with tension."
        ],
        "hard": [
            f"{player_name} confronts you directly with intensity.",
            f"An unexpected revelation about {player_name} strikes you.",
            f"{player_name}'s actions have serious consequences.",
            "A shocking twist disrupts everything you thought.",
            "The stakes have never felt higher..."
        ]
    }
    
    import random
    events_for_difficulty = narratives.get(difficulty, narratives["normal"])
    return random.choice(events_for_difficulty)

