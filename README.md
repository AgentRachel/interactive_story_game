# Interactive Story Game

## Clone Repository

```bash
git clone https://github.com/AgentRachel/interactive_story_game.git
cd interactive_story_game
```

## Setup (VS Code)

1. Create virtual environment:

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install fastapi uvicorn websockets sqlalchemy jinja2 pdfkit weasyprint openai
```

Optional for image generation:

```bash
pip install diffusers transformers torch torchvision
```

3. Run backend server:

```bash
uvicorn backend.main:app --reload
```

4. Open `frontend/index.html` in your browser.

5. To join multiple players, open the frontend in another browser tab/device and enter a different name.

## Features

* Story Mode (1–max characters)
* Game Mode (2–8 players, AI slots optional)
* Secret roles + personal objectives
* Room-based spatial awareness + sound propagation
* Whisper chat + filtered event visibility
* Prebuilt + AI-generated + advanced AI map system
* Visual board-game UI with icons and minimal text
* PDF export of story/game
* Difficulty presets and AI escalation options
* Multi-device support on local network
