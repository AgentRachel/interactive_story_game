// Game state
let gameState = {
    playerId: null,
    currentRoom: null,
    role: null,
    playerCount: 0,
    events: [],
    chatMessages: [],
    connectedRooms: [],
    allRooms: ["Library", "Kitchen", "Hallway", "Basement", "Attic"]
};

// WebSocket connection
let socket = null;

// Initialize on page load
window.addEventListener('load', function() {
    const playerId = prompt("Enter your player name:") || `Player_${Math.random().toString(36).substr(2, 9)}`;
    gameState.playerId = playerId;
    
    connectToServer(playerId);
});

function connectToServer(playerId) {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/${playerId}`;
    
    console.log(`Connecting to ${wsUrl}...`);
    socket = new WebSocket(wsUrl);
    
    socket.onopen = function(event) {
        console.log("Connected to server");
        updateStatus("Connected", true);
    };
    
    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        console.log("Received:", data);
        handleMessage(data);
    };
    
    socket.onerror = function(error) {
        console.error("WebSocket error:", error);
        updateStatus("Error", false);
    };
    
    socket.onclose = function(event) {
        console.log("Disconnected from server");
        updateStatus("Disconnected", false);
    };
}

function handleMessage(data) {
    const type = data.type;
    
    if (type === "welcome") {
        handleWelcome(data);
    } else if (type === "events") {
        handleEvents(data.events);
    } else if (type === "player_moved") {
        addEvent({
            type: "movement",
            player: data.player,
            room: data.room
        });
    } else if (type === "player_joined") {
        const player = data.player;
        addEvent({
            type: "join",
            player: player.name
        });
        gameState.playerCount = data.total_players;
        updatePlayerCount();
    } else if (type === "player_left") {
        addEvent({
            type: "leave",
            player: data.player
        });
        gameState.playerCount = data.total_players;
        updatePlayerCount();
    } else if (type === "chat") {
        addChatMessage(data.player, data.message);
    }
}

function handleWelcome(data) {
    const player = data.player;
    gameState.currentRoom = player.current_room;
    gameState.role = player.role;
    gameState.playerCount = player.current_room ? 1 : 0;
    
    updatePlayerInfo();
    updateConnectedRooms();
    updatePlayerCount();
    
    addEvent({
        type: "system",
        message: `Welcome ${player.name}! You are in the ${player.current_room}.`
    });
}

function handleEvents(events) {
    if (!events || events.length === 0) return;
    
    events.forEach(event => {
        if (event.type === "ai_event") {
            addEvent({
                type: "ai",
                message: event.text,
                room: event.room
            });
        } else if (event.type === "move") {
            addEvent({
                type: "movement",
                player: event.player,
                room: event.room
            });
        } else if (event.type === "chat") {
            addChatMessage(event.player, event.message);
        } else if (event.type === "whisper") {
            addChatMessage(event.player, `*whispers* ${event.message}`, true);
        } else {
            addEvent(event);
        }
    });
}

function addEvent(event) {
    const container = document.getElementById("events-container");
    const eventEl = document.createElement("div");
    eventEl.className = `event event-${event.type || 'general'}`;
    
    let text = "";
    const timestamp = new Date().toLocaleTimeString();
    
    switch(event.type) {
        case "system":
            text = `[${timestamp}] 📢 ${event.message}`;
            break;
        case "movement":
            text = `[${timestamp}] 🚶 ${event.player} moved to ${event.room}`;
            break;
        case "join":
            text = `[${timestamp}] ✨ ${event.player} joined the game`;
            break;
        case "leave":
            text = `[${timestamp}] 👋 ${event.player} left the game`;
            break;
        case "ai":
            text = `[${timestamp}] ⚡ AI Event: ${event.message}`;
            break;
        default:
            text = `[${timestamp}] ${JSON.stringify(event)}`;
    }
    
    eventEl.textContent = text;
    container.appendChild(eventEl);
    container.scrollTop = container.scrollHeight;
    
    gameState.events.push(event);
}

function addChatMessage(player, message, whisper = false) {
    const container = document.getElementById("chat-messages");
    const msgEl = document.createElement("div");
    msgEl.className = `chat-message ${whisper ? 'whisper' : 'normal'}`;
    
    const timestamp = new Date().toLocaleTimeString();
    msgEl.innerHTML = `<strong>[${timestamp}] ${player}:</strong> ${whisper ? '<em>' : ''}${message}${whisper ? '</em>' : ''}`;
    
    container.appendChild(msgEl);
    container.scrollTop = container.scrollHeight;
    
    gameState.chatMessages.push({ player, message, timestamp });
}

function updatePlayerInfo() {
    document.getElementById("player-name").textContent = gameState.playerId;
    document.getElementById("player-room").textContent = gameState.currentRoom || "-";
    document.getElementById("player-role").textContent = gameState.role || "None";
}

function updateConnectedRooms() {
    // In a real game, this would come from the server
    // For now, show all rooms as "connected" via hallway
    const container = document.getElementById("room-buttons");
    container.innerHTML = "";
    
    gameState.allRooms.forEach(room => {
        if (room !== gameState.currentRoom) {
            const btn = document.createElement("button");
            btn.textContent = room;
            btn.className = "room-button";
            btn.onclick = () => moveTo(room);
            container.appendChild(btn);
        }
    });
}

function updatePlayerCount() {
    document.getElementById("player-count").textContent = gameState.playerCount;
}

function moveTo(room) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        alert("Not connected to server");
        return;
    }
    
    gameState.currentRoom = room;
    updatePlayerInfo();
    updateConnectedRooms();
    
    socket.send(JSON.stringify({
        type: "move",
        room: room
    }));
}

function sendChat() {
    const input = document.getElementById("chat-input");
    const message = input.value.trim();
    
    if (!message) return;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        alert("Not connected to server");
        return;
    }
    
    socket.send(JSON.stringify({
        type: "chat",
        message: message,
        whisper: false
    }));
    
    addChatMessage("You", message);
    input.value = "";
}

function handleChatKeypress(event) {
    if (event.key === "Enter") {
        sendChat();
    }
}

function whisper() {
    const target = prompt("Whisper to whom?");
    const message = prompt("What do you say?");
    
    if (!target || !message || !socket || socket.readyState !== WebSocket.OPEN) return;
    
    socket.send(JSON.stringify({
        type: "chat",
        message: message,
        whisper: true,
        target: target
    }));
    
    addChatMessage("You", `*whispers to ${target}* ${message}`, true);
}

function investigate() {
    socket.send(JSON.stringify({
        type: "ability",
        ability: "Investigate"
    }));
    addEvent({
        type: "ability",
        message: "You investigate your surroundings..."
    });
}

function hide() {
    socket.send(JSON.stringify({
        type: "ability",
        ability: "Hide"
    }));
    addEvent({
        type: "ability",
        message: "You hide!"
    });
}

function updateStatus(status, connected) {
    const statusEl = document.getElementById("status");
    statusEl.textContent = status;
    statusEl.className = `status ${connected ? 'connected' : 'disconnected'}`;
}

// Initialize map display
function updateMapDisplay() {
    const mapDisplay = document.getElementById("map-display");
    mapDisplay.innerHTML = gameState.allRooms.map(room => 
        `<div class="room-tile ${room === gameState.currentRoom ? 'active' : ''}">${room}</div>`
    ).join("");
}

// Update map when room changes
window.addEventListener('load', updateMapDisplay);

