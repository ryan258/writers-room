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

/agent-swarm-writers-room
│
├── main.py              # The orchestrator (game loop)
├── agents.py            # The Agent class definition & OpenRouter API logic
├── personalities.py     # The System Prompts (The "Soul" of the agents)
├── .env                 # API Keys (gitignored)
├── requirements.txt     # Dependencies
├── transcripts/         # Folder to save the chaotic outputs
│
├── web/                 # Web interface (Phase 5)
│   ├── app.py           # Flask/FastAPI backend
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css        # Dark theme styling
│   │   ├── js/
│   │   │   └── app.js           # Frontend logic
│   │   └── images/
│   │       ├── toaster.svg      # Agent Bob icon
│   │       └── skull-tequila.svg # Agent RIP icon
│   └── templates/
│       └── index.html   # Main UI (based on ui.png design)
│
└── ui.png               # UI design reference


3. Configuration (OpenRouter)

We are using OpenRouter to access diverse models without paying for distinct subscriptions.

Environment Variables (.env):

OPENROUTER_API_KEY=sk-or-v1-...
YOUR_SITE_URL=http://localhost  # Required by OpenRouter for rankings
YOUR_SITE_NAME=AgentSwarmLocal


Recommended Model Mapping (Free/Cheap Tier):

All agents are currently configured to use `nvidia/nemotron-nano-12b-v2-vl:free` (a visual-language model), but this can be changed in `personalities.py`.

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

Turn 1-5: The legendary writers add their unique spin (Serling's moral, King's backstory, Lovecraft's dread, Borges' paradox, Stack's mystery).

Turn 6: RIP Tequila Bot interrupts to suggest where the bottle placement goes.

Rounds: The cycle repeats for 3 rounds.

Key Feature - The "Context Window":
Pass the previous turns to the current agent so they can "react" to each other.

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
    python main.py
    ```

4.  **Deactivate when done:**
    ```bash
    deactivate
    ```

7. Future Expansions

The "Producer" Agent: An LLM that judges who "won" the argument and fires one of the writers.

TTS Integration: Pipe the output to ElevenLabs or OpenAI TTS to hear them argue in character.

Web Interface: A simple Streamlit app to visualize the chat bubbles.