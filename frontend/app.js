// Game state
let gameState = {
    playerId: null,
    currentRoom: null,
    role: null,
    playerCount: 0,
    events: [],
    chatMessages: [],
    connectedRooms: [],
    allRooms: ["Library", "Kitchen", "Hallway", "Basement", "Attic"],
    gameMode: null  // "story" or "game"
};

// WebSocket connection
let socket = null;

// Initialize on page load - show welcome screen
window.addEventListener('load', function() {
    // Welcome screen is shown by default, hide game screen
    document.getElementById('game-screen').classList.add('hidden');
});

function handleNameKeypress(event) {
    if (event.key === 'Enter') {
        const mode = event.target.dataset.mode;
        if (mode === 'story') startStory();
        else if (mode === 'game') startGame();
    }
}

function startStory() {
    // Show story menu instead of joining immediately
    document.getElementById('story-menu').classList.remove('hidden');
}

function saveStory() {
    // trigger backend save (session autosave)
    fetch('/game/save-session?session_name=story_autosave', { method: 'POST' })
        .then(r => r.json())
        .then(j => alert('Story saved'))
        .catch(e => alert('Save failed'));
}

function exportPDF() {
    // open PDF export in new window/tab
    window.open('/game/export-pdf', '_blank');
}

function backToWelcome() {
    document.getElementById('story-menu').classList.add('hidden');
}

function showNewStoryForm() {
    const menu = document.getElementById('story-menu');
    menu.innerHTML = `
        <h3>Create New Story</h3>
        <div class="new-story-form">
            <label>World: <input id="new-world" value="default"></label><br>
            <label>Character: <input id="new-character" value="Player"></label><br>
            <label>Genre: <select id="new-genre"><option>mystery</option><option>horror</option><option>fantasy</option></select></label><br>
            <label>Advanced (JSON):<br><textarea id="new-advanced" rows="4" cols="30"></textarea></label><br>
            <button onclick="createStory()">Create & Start</button>
            <button onclick="window.location.reload()">Cancel</button>
        </div>
    `;
}

async function createStory() {
    const world = document.getElementById('new-world').value || 'default';
    const character = document.getElementById('new-character').value || gameState.playerId || 'Player';
    const genre = document.getElementById('new-genre').value || 'mystery';
    const advanced = document.getElementById('new-advanced').value || '';

    try {
        const resp = await fetch(`/story/new?world=${encodeURIComponent(world)}&character=${encodeURIComponent(character)}&genre=${encodeURIComponent(genre)}&advanced=${encodeURIComponent(advanced)}`, { method: 'POST' });
        const data = await resp.json();
        if (data.room_code) {
            gameState.storyRoomCode = data.room_code;
            alert(`Story created. Room code: ${data.room_code}`);
            // proceed to join as story player
            const playerName = document.getElementById('player-name-input').value.trim() || character;
            joinGame(playerName, 'story');
        } else {
            alert('Failed to create story');
        }
    } catch (e) {
        console.error(e);
        alert('Error creating story');
    }
}

async function showContinueStories() {
    try {
        const resp = await fetch('/story/list');
        const data = await resp.json();
        const menu = document.getElementById('story-menu');
        if (!data.sessions || Object.keys(data.sessions).length === 0) {
            menu.innerHTML = '<p>No saved stories found.</p><button onclick="window.location.reload()">Back</button>';
            return;
        }
        let html = '<h3>Select a story to continue</h3>';
        for (const [code, s] of Object.entries(data.sessions)) {
            html += `<div class="story-entry">Room: ${code} - World: ${s.world} - Character: ${s.character} <button onclick="joinStory('${code}')">Join</button></div>`;
        }
        html += '<button onclick="window.location.reload()">Back</button>';
        menu.innerHTML = html;
    } catch (e) {
        console.error(e);
        alert('Error fetching stories');
    }
}

function manageStories() {
    alert('Story/world management UI coming soon');
}

function enterRoomCode() {
    const code = prompt('Enter room code:');
    if (!code) return;
    gameState.storyRoomCode = code.trim();
    const playerName = document.getElementById('player-name-input').value.trim() || 'Player';
    joinGame(playerName, 'story');
}

function joinStory(code) {
    gameState.storyRoomCode = code;
    const playerName = document.getElementById('player-name-input').value.trim() || 'Player';
    joinGame(playerName, 'story');
}

function startGame() {
    const playerName = document.getElementById('player-name-input').value.trim();
    if (!playerName) {
        alert('Please enter a name');
        return;
    }
    joinGame(playerName, 'game');
}

function joinGame(playerName, mode) {
    gameState.playerId = playerName;
    gameState.gameMode = mode;
    
    // Hide welcome screen and show game screen
    document.getElementById('welcome-screen').classList.add('hidden');

    if (mode === 'story') {
        document.getElementById('story-screen').classList.remove('hidden');
        document.getElementById('game-screen').classList.add('hidden');
    } else {
        document.getElementById('game-screen').classList.remove('hidden');
        document.getElementById('story-screen').classList.add('hidden');
    }

    // Connect to server
    connectToServer(playerName, mode);
}

function connectToServer(playerId, mode) {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Determine backend host/port.
    // If the page is served from a different port (e.g. Live Server on 5500), prefer the backend on port 8001.
    const defaultBackendPort = '8001';
    const hostname = window.location.hostname || 'localhost';
    const pagePort = window.location.port || '';
    let host;
    if (!pagePort) {
        // file:// or unknown -> use localhost:8001
        host = `${hostname}:${defaultBackendPort}`;
    } else if (pagePort !== defaultBackendPort) {
        // Page is served from a different port (e.g., 5500). Connect to backend port directly.
        host = `${hostname}:${defaultBackendPort}`;
    } else {
        // Page is served from same backend port
        host = window.location.host;
    }
    let wsUrl = `${wsProtocol}//${host}/ws/${playerId}`;
    if (mode === 'story' && gameState.storyRoomCode) {
        wsUrl += `?room=${encodeURIComponent(gameState.storyRoomCode)}`;
    }
    // tell server the selected mode/difficulty (best-effort)
    try {
        const difficulty = document.getElementById('difficulty-select') ? document.getElementById('difficulty-select').value : 'normal';
        fetch(`/game/mode?mode=${encodeURIComponent(mode)}&difficulty=${encodeURIComponent(difficulty)}`, { method: 'POST' }).catch(()=>{});
    } catch(e) {}

    console.log(`Connecting to ${wsUrl} in ${mode} mode...`);
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
        // Help the user: suggest running the backend if connection fails
        const statusEl = document.getElementById('status');
        if (statusEl && (statusEl.textContent === 'Connecting...' || statusEl.textContent === 'Error')) {
            statusEl.title = `Tried to connect to ${wsUrl}. Ensure backend is running and you opened the page via http://localhost:8001/ (not file://).`;
        }
    };
    
    socket.onclose = function(event) {
        console.log("Disconnected from server");
        updateStatus("Disconnected", false);
        // show brief guidance if connection closed immediately
        if (!event.wasClean) {
            alert('Disconnected from server. Make sure the backend is running (uvicorn backend.main:app --reload --port 8001) and you opened the game from http://localhost:8001/');
        }
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
    // Use server-authoritative player info
    gameState.playerId = player.name || gameState.playerId;
    gameState.currentRoom = player.current_room;
    gameState.role = player.role;
    // Use server-provided counts if available
    gameState.playerCount = data.total_players || Object.keys(gameState.players || {}).length || 1;
    gameState.playerIndex = data.player_index || 1;
    gameState.abilities = player.abilities || [];
    gameState.personal_objective = player.personal_objective || '';
    
    updatePlayerInfo();
    updateConnectedRooms();
    updatePlayerCount();
    updateAbilities();
    updateRoleObjective();
    updateMapDisplay();
    
    addEvent({
        type: "system",
        message: `Welcome ${player.name}! You are Player ${gameState.playerIndex} and are in the ${player.current_room}.`
    });
    // If story mode, show room code prominently
    if (gameState.gameMode === 'story' && data.room_code) {
        const title = document.getElementById('story-title');
        const narrative = document.getElementById('narrative-text');
        title.textContent = `Story Room: ${data.room_code}`;
        narrative.textContent = `You are connected to story room ${data.room_code}. The AI will begin shortly.`;
    }
}

function handleEvents(events) {
    if (!events || events.length === 0) return;
    
    events.forEach(event => {
        // Story mode transforms AI events into immersive narrative
        if (gameState.gameMode === 'story' && event.type === "ai_event") {
            displayNarrative(event.text);
            return;
        }

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
    // show server-provided player number if available
    document.getElementById("player-number").textContent = gameState.playerIndex || '-';
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

// ---- Story mode helpers ----
function displayNarrative(text) {
    const narrative = document.getElementById('narrative-text');
    // Chunk long narrative into short paragraphs (ADHD-friendly)
    const sentences = text.split(/(?<=[.?!])\s+/).filter(s => s.trim().length > 0);
    let short = '';
    for (let i=0;i<Math.min(3, sentences.length);i++) short += sentences[i] + ' ';
    short = short.trim();
    narrative.textContent = short;
    // optional detail toggles could show more
    // simple choice generation (can be replaced with richer logic)
    const choices = ["Investigate", "Ignore", "Approach"];
    presentChoices(choices);
}

function presentChoices(choices) {
    const container = document.getElementById('choice-buttons');
    container.innerHTML = '';
    choices.forEach(ch => {
        const btn = document.createElement('button');
        btn.textContent = ch;
        btn.onclick = () => handleChoice(ch);
        container.appendChild(btn);
    });
}

function handleChoice(choice) {
    addEvent({ type: 'system', message: `You chose: ${choice}` });
    // send choice to server as an ability or chat to influence story
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'ability', ability: choice }));
    }
    // provide immediate feedback and clear choices
    const narrative = document.getElementById('narrative-text');
    narrative.textContent = `You chose to ${choice.toLowerCase()}. The story unfolds...`;
    document.getElementById('choice-buttons').innerHTML = '';
}

function endStory() {
    // return to welcome screen
    document.getElementById('story-screen').classList.add('hidden');
    document.getElementById('welcome-screen').classList.remove('hidden');
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.close();
    }
}

function updateAbilities() {
    // Show player's abilities (filled if backend provides them)
    const info = document.getElementById('player-info');
    let ab = gameState.abilities || [];
    let list = info.querySelector('.abilities-list');
    if (!list) {
        list = document.createElement('div');
        list.className = 'abilities-list';
        info.appendChild(list);
    }
    list.innerHTML = `Abilities: ${ab.length ? ab.join(', ') : 'None'}`;
}

function updateRoleObjective() {
    const info = document.getElementById('player-info');
    let obj = gameState.personal_objective || '';
    let el = info.querySelector('.objective');
    if (!el) {
        el = document.createElement('div');
        el.className = 'objective';
        info.appendChild(el);
    }
    el.innerHTML = obj ? `<strong>Objective:</strong> ${obj}` : '';
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
    // render compact tiles; include a player icon for current room
    mapDisplay.innerHTML = gameState.allRooms.map(room => {
        const active = room === gameState.currentRoom ? 'active' : '';
        const playerIcon = room === gameState.currentRoom ? `<div class="player-icon">👤</div>` : '';
        return `<div class="room-tile ${active}">${room}${playerIcon}</div>`;
    }).join("");
}

// Update map when room changes
window.addEventListener('load', updateMapDisplay);

