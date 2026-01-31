Agent Swarm Writers Room: The "Mischief" Engine (Legendary Edition)

1. Project Overview

This project is a Python-based "Writers Room" simulation where multiple AI agents, each with a radically different personality and writing style, collaborate (and argue) over a single creative prompt.

The Goal: To generate absurdist, conflicting narratives by pitting legendary writers against each other (and a Deranged Marketing exec).

The Tech Stack:

Language: Python 3.10+

API Provider: OpenRouter (Allows mixing and matching free/cheap models).

Library: openai (Python client, compatible with OpenRouter endpoints).

2. Architecture & File Structure

The project is built with the following structure to keep the logic clean and modular.

/writers-room
│
├── main.py              # The CLI orchestrator (game loop)
├── lib/                 # Core logic (portable Arsenal modules)
│   ├── agents.py        # Agent class definition & OpenRouter API logic
│   ├── personalities.py # System prompts (the "Soul" of the agents)
│   ├── session.py       # Session orchestration
│   ├── story_state.py   # Center Table story state
│   └── voice.py         # Optional TTS support
├── debug_model.py       # Testing utility for model behavior
├── .env                 # API Keys (gitignored)
├── .env.example         # Template for environment variables
├── requirements.txt     # Dependencies
├── transcripts/         # Folder to save the chaotic outputs (auto-created)
│
├── web/                 # Web interface
│   ├── app.py           # FastAPI backend + WebSocket handlers
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css        # Dark theme styling
│   │   └── js/
│   │       └── app.js           # Frontend WebSocket logic
│   └── templates/
│       └── index.html   # Main UI
│
├── README.md            # This file
├── SETUP.md             # Detailed setup instructions
├── ROADMAP.md           # Development phases and future plans
├── PHASE1_COMPLETE.md   # Phase 1 summary
├── PHASE2_COMPLETE.md   # Phase 2 features and usage
├── PHASE3_COMPLETE.md   # Phase 3 Producer agent
├── PHASE5_COMPLETE.md   # Phase 5 web interface
└── CHANGELOG.md         # Version history


3. Configuration (OpenRouter)

We are using OpenRouter to access diverse models without paying for distinct subscriptions.

Environment Variables (.env):

OPENROUTER_API_KEY=sk-or-v1-...
YOUR_SITE_URL=http://localhost  # Required by OpenRouter for rankings
YOUR_SITE_NAME=AgentSwarmLocal


Recommended Model Mapping (Free/Cheap Tier):

All agents are currently configured to use `mistralai/ministral-3b-2512` (a free/cheap fast model), but this can be changed in `personalities.py` or overridden with the `-m` flag.

4. The Agents (System Prompts)

This is the most critical section. These prompts define the "Mischief."

1. Rod Serling ("The Twilight Zone")
   - Focus: Irony, moral lessons, twists.
   - Style: Dramatic narration, "fifth dimension" references.

2. Stephen King ("The Master of Horror")
   - Focus: Character backstories, childhood trauma, small-town secrets.
   - Style: Character-driven, slow burn.

3. H.P. Lovecraft ("The Void Scrivener")
   - Focus: Cosmic dread, ancient gods, forbidden knowledge.
   - Style: Archaic language, "non-Euclidean" descriptions.

4. Jorge Luis Borges ("The Labyrinth Maker")
   - Focus: Philosophical paradoxes, infinite libraries, mirrors.
   - Style: Intellectual, meta-fictional, circular.

5. Robert Stack ("Unsolved Mysteries")
   - Focus: True crime vibes, spooky unanswered questions.
   - Style: Ominous voice-over, "Update!"

6. RIP Tequila Bot ("The Chaos Agent")
   - Focus: PRODUCT PLACEMENT.
   - Style: Deranged marketing executive. Catchphrase: "Time to RIP!"

5. The Logic Flow (main.py)

The script runs in a "Round Robin" conversation loop.

User Input: User provides a seed prompt (e.g., "A man discovers a mysterious door in his basement.")

Turn 1-6: All six agents respond in order:
1. Rod Serling - adds ironic moral twist
2. Stephen King - develops character backstory/horror
3. H.P. Lovecraft - introduces cosmic dread
4. Jorge Luis Borges - creates philosophical paradox
5. Robert Stack - poses eerie mystery question
6. RIP Tequila Bot - inserts shameless product placement

Rounds: The cycle repeats for a configurable number of rounds (user is prompted, or use `-r` flag).

Key Feature - The "Context Window":
Each agent sees the original user prompt plus the last 4 messages, allowing them to react to recent developments while staying on topic.

6. Quick Start (Activation & Running)

Follow these steps to get the writers room running:

1.  **Set up the environment:**
    ```bash
    # Create virtual environment
    python3 -m venv venv
    
    # Activate it (Mac/Linux)
    source venv/bin/activate
    # OR Windows: venv\Scripts\activate
    
    # Install dependencies
    pip install -r requirements.txt
    ```

2.  **Configure API Key:**
    ```bash
    cp .env.example .env
    # Edit .env and paste your OpenRouter API Key
    ```

3.  **Run the Simulation:**
    ```bash
    # Basic usage
    python main.py

    # With Phase 2 options
    python main.py -r 5 -t 1.2  # 5 rounds, more creative
    python main.py --help       # See all options
    ```

4.  **Deactivate when done:**
    ```bash
    deactivate
    ```

## Phase 2 Features

- **Configurable Rounds**: Choose how many rounds to run
- **Continue Option**: Keep going after rounds complete
- **Model Override**: Try different models (`-m` flag)
- **Temperature Control**: Adjust creativity (`-t` flag, 0.0-2.0)
- **API Validation**: Automatic key validation on startup
- **Better Error Handling**: Clear, helpful error messages

See `PHASE2_COMPLETE.md` for full documentation.

## Phase 3 Features

- **The Producer**: A snarky Hollywood executive judges all writers after each round
- **Scoring System**: Each writer receives 1-10 scores with commentary
- **Live Leaderboards**: See rankings with medals (🥇🥈🥉) after every round
- **Winner Declaration**: Final leaderboard and winner announcement
- **Fire Worst Performer**: Optional `--fire-worst` flag to terminate the lowest scorer
- **Disable Producer**: Use `--no-producer` to run without judging

See `PHASE3_COMPLETE.md` for full documentation.

## Phase 5 Features (New! 🌐)

- **Dark-Themed Web UI**: Beautiful black/purple gradient interface
- **Real-Time Streaming**: Watch agents think and respond live via WebSockets
- **Agent Cards**: Six color-coded writer cards plus Producer in responsive grid
- **Live Leaderboards**: Visual rankings with medals update automatically
- **Configuration Panel**: Control rounds, temperature, Producer, and fire-worst
- **Status Tracking**: Live updates showing current round and activity
- **Winner Animations**: Dramatic winner and loser announcements

**Quick Start**: `cd web && python app.py` then visit http://localhost:5000

See `PHASE5_COMPLETE.md` for full documentation.

7. Future Expansions

TTS Integration: Pipe the output to ElevenLabs or OpenAI TTS to hear them argue in character (Phase 4).

Web Interface: A dark-themed web UI with agent cards and live leaderboards (Phase 5).

Custom Agents: Let users create their own agent personalities and story modes (Phase 6).

See `ROADMAP.md` for the full development plan.
