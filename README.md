# Writers Room

Writers Room is a bare-metal Python storytelling workshop where a fixed roster of AI writers collaborate on one prompt. It ships with a terminal CLI and a FastAPI + WebSocket web interface, plus custom-agent management and shared story-state tracking.

## Stack

- Python 3.10+
- OpenRouter for text generation
- FastAPI + Jinja2 + native WebSocket for the web UI
- File-based persistence for custom agents and transcripts
- Optional TTS via OpenAI, ElevenLabs, or `pyttsx3`

## What Ships

- CLI session runner in [`main.py`](/Users/ryanjohnson/Projects/writers-room/main.py)
- Web UI in [`web/app.py`](/Users/ryanjohnson/Projects/writers-room/web/app.py) on port `5001`
- Shared Center Table story-state engine in [`lib/story_state.py`](/Users/ryanjohnson/Projects/writers-room/lib/story_state.py)
- Session orchestration in [`lib/session.py`](/Users/ryanjohnson/Projects/writers-room/lib/session.py)
- Custom agent CRUD in [`lib/custom_agents.py`](/Users/ryanjohnson/Projects/writers-room/lib/custom_agents.py) and [`web/templates/agents.html`](/Users/ryanjohnson/Projects/writers-room/web/templates/agents.html)
- Automatic transcript saving for both CLI and web sessions into `transcripts/`
- Pytest suite covering agents, session orchestration, story state, custom agents, and the web API

## Quick Start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `OPENROUTER_API_KEY` in `.env`. `OPENAI_API_KEY` and `ELEVENLABS_API_KEY` are only needed if you want experimental voice playback.

### Run the CLI

```bash
./start.sh
```

Or:

```bash
python main.py
```

### Run the Web UI

```bash
./start_web.sh
```

Or:

```bash
uvicorn web.app:app --reload --port 5001
```

Open [http://localhost:5001](http://localhost:5001).

## Tests

```bash
python3 -m pytest
```

`pytest.ini` restricts discovery to the real `tests/` suite so the legacy manual verification scripts at repo root are not collected.

## Operational Notes

- The web server supports one active session at a time. Session state is held in-process in [`web/app.py`](/Users/ryanjohnson/Projects/writers-room/web/app.py).
- Voice playback is experimental. The UI labels it explicitly and disables the toggle when no provider is configured.
- The web client now reconnects its WebSocket automatically after disconnects, but missed events during downtime are not replayed.
- Historical phase/fix markdown files were archived to `docs/archive/` to keep the repo surface clean.

## Key Files

- [`main.py`](/Users/ryanjohnson/Projects/writers-room/main.py): CLI entrypoint
- [`start.sh`](/Users/ryanjohnson/Projects/writers-room/start.sh): CLI launcher
- [`start_web.sh`](/Users/ryanjohnson/Projects/writers-room/start_web.sh): web launcher
- [`lib/agents.py`](/Users/ryanjohnson/Projects/writers-room/lib/agents.py): OpenRouter client and context trimming
- [`lib/session.py`](/Users/ryanjohnson/Projects/writers-room/lib/session.py): web session lifecycle, producer scoring, transcript persistence
- [`web/static/js/app.js`](/Users/ryanjohnson/Projects/writers-room/web/static/js/app.js): WebSocket client, UI event handling, audio queue
- [`tests/test_web_app.py`](/Users/ryanjohnson/Projects/writers-room/tests/test_web_app.py): API coverage for custom-agent CRUD
