"""
Test Script: Auto-connect 3 players and demonstrate all features
- Room awareness
- AI events
- Event filtering
- Spatial awareness
- Chat/whisper system
"""

import asyncio
import json
import websockets
from datetime import datetime

class TestPlayer:
    def __init__(self, name, player_id):
        self.name = name
        self.player_id = player_id
        self.websocket = None
        self.events = []
        self.room = None
        self.role = None
        
    async def connect(self, uri):
        """Connect to game server"""
        try:
            self.websocket = await websockets.connect(uri)
            print(f"[{self.name}] Connected to server")
            return True
        except Exception as e:
            print(f"[{self.name}] Connection failed: {e}")
            return False
    
    async def listen(self):
        """Listen for messages from server"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                self.events.append(data)
                self.print_event(data)
        except websockets.exceptions.ConnectionClosed:
            print(f"[{self.name}] Disconnected")
    
    async def send_action(self, action):
        """Send action to server"""
        try:
            await self.websocket.send(json.dumps(action))
        except Exception as e:
            print(f"[{self.name}] Error sending action: {e}")
    
    def print_event(self, data):
        """Pretty print event"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        msg_type = data.get("type", "unknown")
        
        if msg_type == "welcome":
            print(f"\n[{timestamp}] {self.name} - Welcome! Role: {data.get('player', {}).get('role', 'None')}")
            self.room = data.get('player', {}).get('current_room')
            
        elif msg_type == "events":
            events = data.get("events", [])
            if events:
                print(f"\n[{timestamp}] {self.name} (in {self.room}) received {len(events)} event(s):")
                for e in events:
                    if e.get("type") == "player_moved":
                        print(f"  → {e.get('player')} moved to {e.get('room')}")
                    elif e.get("type") == "ai_event":
                        print(f"  ⚡ AI: {e.get('text')}")
                    elif e.get("type") == "chat":
                        print(f"  💬 {e.get('player')}: {e.get('message')}")
                    else:
                        print(f"  • {e.get('type')}: {e.get('text', '')}")
        
        elif msg_type == "player_moved":
            print(f"\n[{timestamp}] {data.get('player')} moved to {data.get('room')}")
            if data.get('player') == self.name:
                self.room = data.get('room')
        
        elif msg_type == "ai_event":
            print(f"\n[{timestamp}] {self.name} detects: ⚡ {data.get('text')}")


async def run_test():
    """Main test scenario"""
    print("=" * 70)
    print("🎮 INTERACTIVE STORY GAME - TEST SCENARIO")
    print("=" * 70)
    print("\nStarting 3 auto-players with spatial awareness...\n")
    
    # Create 3 test players
    players = [
        TestPlayer("Alice", "alice"),
        TestPlayer("Bob", "bob"),
        TestPlayer("Charlie", "charlie"),
    ]
    
    uri = "ws://localhost:8000/ws"
    
    # Connect all players
    print("\n[PHASE 1] Connecting players...\n")
    for player in players:
        success = await player.connect(f"{uri}/{player.player_id}")
        if not success:
            print("\n❌ Could not connect to server. Make sure backend is running:")
            print("   uvicorn backend.main:app --reload")
            return
    
    # Start listening tasks
    listen_tasks = [asyncio.create_task(player.listen()) for player in players]
    
    await asyncio.sleep(1)  # Wait for connections to establish
    
    # Phase 2: Start game
    print("\n[PHASE 2] Starting game...\n")
    
    # Phase 3: Movements to demonstrate room awareness
    print("\n[PHASE 3] Testing room-based spatial awareness...\n")
    
    await asyncio.sleep(1)
    
    # Alice stays in Library
    print("\n→ Alice stays in Library (starting room)")
    
    await asyncio.sleep(1)
    
    # Bob moves to Kitchen
    print("→ Bob moves to Kitchen")
    await players[1].send_action({
        "type": "move",
        "room": "Kitchen"
    })
    
    await asyncio.sleep(2)
    
    # Charlie moves to Basement
    print("→ Charlie moves to Basement")
    await players[2].send_action({
        "type": "move",
        "room": "Basement"
    })
    
    await asyncio.sleep(2)
    
    # Phase 4: Chat demonstration
    print("\n[PHASE 4] Testing chat system (same room, different room)...\n")
    
    # Alice sends message in Library
    await players[0].send_action({
        "type": "chat",
        "message": "Is anyone here?"
    })
    
    await asyncio.sleep(2)
    
    # Bob sends message in Kitchen (should NOT be seen by Alice)
    await players[1].send_action({
        "type": "chat",
        "message": "Hello from the Kitchen!"
    })
    
    await asyncio.sleep(2)
    
    # Phase 5: More movements
    print("\n[PHASE 5] Testing event propagation with movement...\n")
    
    # Alice moves to Hallway
    print("→ Alice moves to Hallway")
    await players[0].send_action({
        "type": "move",
        "room": "Hallway"
    })
    
    await asyncio.sleep(2)
    
    # Bob moves to Hallway
    print("→ Bob moves to Hallway (meets Alice)")
    await players[1].send_action({
        "type": "move",
        "room": "Hallway"
    })
    
    await asyncio.sleep(1)
    
    # They chat now
    await players[0].send_action({
        "type": "chat",
        "message": "Oh, I found you!"
    })
    
    await asyncio.sleep(2)
    
    # Phase 6: Watch AI events
    print("\n[PHASE 6] Observing AI event generation (watch for ⚡ events)...\n")
    print("Waiting 15 seconds for AI events to occur...\n")
    
    await asyncio.sleep(15)
    
    # Phase 7: Summary
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETE")
    print("=" * 70)
    print("\n📊 Summary:")
    for i, player in enumerate(players, 1):
        print(f"\n{i}. {player.name}:")
        print(f"   - Current Room: {player.room}")
        print(f"   - Events Received: {len(player.events)}")
        if player.events:
            print(f"   - Last Event: {player.events[-1].get('type')}")
    
    print("\n🔍 What to verify:")
    print("  ✓ Players in same room see each other's chat/movement")
    print("  ✓ Players in different rooms DON'T see each other's chat")
    print("  ✓ AI events appear in rooms periodically")
    print("  ✓ Event filters prevent wrong players from seeing events")
    print("  ✓ WebSocket communication is working")
    
    print("\n" + "=" * 70 + "\n")
    
    # Close connections
    for player in players:
        if player.websocket:
            await player.websocket.close()


if __name__ == "__main__":
    print("\n🚀 Interactive Story Game - Automated Test\n")
    print("Prerequisites:")
    print("  1. Backend running: uvicorn backend.main:app --reload")
    print("  2. Install dependencies: pip install fastapi uvicorn websockets")
    print("\nStarting test in 3 seconds...\n")
    
    try:
        asyncio.run(asyncio.wait_for(run_test(), timeout=120))
    except asyncio.TimeoutError:
        print("\n⏱️ Test timed out after 120 seconds")
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
