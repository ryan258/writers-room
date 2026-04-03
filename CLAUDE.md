# CLAUDE.md

This repository is Writers Room, not the agriculture project previously described here.

## Product Summary

Writers Room is a Python storytelling workshop with:

- CLI entrypoint in [`main.py`](/Users/ryanjohnson/Projects/writers-room/main.py)
- FastAPI + Jinja2 + WebSocket web UI in [`web/app.py`](/Users/ryanjohnson/Projects/writers-room/web/app.py)
- Core portable logic in `lib/`
- File-based storage for custom agents and transcripts
- Optional, explicitly experimental TTS support in [`lib/voice.py`](/Users/ryanjohnson/Projects/writers-room/lib/voice.py)

## Commands

Run the CLI:

```bash
./start.sh
```

Run the web UI:

```bash
./start_web.sh
```

Run tests:

```bash
pytest
```

Direct entrypoints:

```bash
python main.py --help
uvicorn web.app:app --reload --port 5001
```

## Architecture

- `lib/agents.py`: OpenRouter-backed agent client and prompt windowing
- `lib/personalities.py`: built-in agent prompts and genre modes
- `lib/story_state.py`: Center Table state tracking
- `lib/session.py`: web session orchestration, scoring, transcript persistence
- `lib/custom_agents.py`: custom agent CRUD and template logic
- `web/templates/`: server-rendered pages
- `web/static/`: vanilla CSS and JavaScript

## Repo Rules

- Keep core logic in `lib/`; do not import `main.py` from `lib/`
- Do not add Docker, Node, React, Vue, or user-account infrastructure
- Preserve the candlelight palette in `web/static/css/style.css`
- Treat voice as experimental unless you have end-to-end provider verification
- Prefer updating the archival docs under `docs/archive/` only when historic context truly matters

## Operational Notes

- The web server supports one live session at a time via in-process global state
- WebSocket reconnect is automatic, but lost events are not replayed
- Web and CLI transcripts are written to `transcripts/`
- See [`AGENTS.md`](/Users/ryanjohnson/Projects/writers-room/AGENTS.md) for repo-wide review and GitNexus rules
