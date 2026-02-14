import json
import os
from datetime import datetime
from pathlib import Path

class Database:
    """Simple JSON-based database for game state persistence"""
    
    def __init__(self, db_path="data"):
        self.db_path = Path(db_path)
        self.db_path.mkdir(exist_ok=True)
        
        self.players_file = self.db_path / "players.json"
        self.sessions_file = self.db_path / "sessions.json"
        self.events_file = self.db_path / "events.json"
    
    def save_player(self, player_data):
        """Save or update player data"""
        players = self.load_players()
        players[player_data["name"]] = {
            **player_data,
            "saved_at": datetime.now().isoformat()
        }
        self._write_json(self.players_file, players)
    
    def load_players(self):
        """Load all saved players"""
        return self._read_json(self.players_file, {})
    
    def get_player(self, player_name):
        """Get specific player data"""
        players = self.load_players()
        return players.get(player_name)
    
    def save_session(self, session_data):
        """Save game session"""
        sessions = self.load_sessions()
        session_id = session_data.get("id", str(datetime.now().timestamp()))
        sessions[session_id] = {
            **session_data,
            "saved_at": datetime.now().isoformat()
        }
        self._write_json(self.sessions_file, sessions)
        return session_id
    
    def load_sessions(self):
        """Load all sessions"""
        return self._read_json(self.sessions_file, {})
    
    def get_session(self, session_id):
        """Get specific session"""
        sessions = self.load_sessions()
        return sessions.get(session_id)
    
    def save_events(self, events, session_id):
        """Save game events for a session"""
        all_events = self._read_json(self.events_file, {})
        all_events[session_id] = events
        self._write_json(self.events_file, all_events)
    
    def get_events(self, session_id):
        """Get events for a session"""
        all_events = self._read_json(self.events_file, {})
        return all_events.get(session_id, [])
    
    def _read_json(self, file_path, default=None):
        """Read JSON file safely"""
        try:
            if file_path.exists():
                with open(file_path, "r") as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
        return default if default is not None else {}
    
    def _write_json(self, file_path, data):
        """Write JSON file safely"""
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except IOError as e:
            print(f"Error writing to {file_path}: {e}")
            return False

# Global database instance
db = Database()
