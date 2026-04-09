# Writers Room

Writers Room is a bare-metal Python storytelling workshop where a fixed roster of AI writers collaborate on one prompt. It ships with a terminal CLI and a FastAPI + WebSocket web interface, plus custom-agent management and shared story-state tracking.

The repo now also supports a `dnd` mode that turns the table into a level 9 D&D 2024 (5.5) session with a dedicated Dungeon Master and a reusable HTML session brief. If the sibling `executive_reporting` component package is installed, Writers Room uses it; otherwise it falls back to a minimal built-in HTML brief.

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
- Final-draft pipeline generation in [`lib/pipeline.py`](/Users/ryanjohnson/Projects/writers-room/lib/pipeline.py)
- Custom agent CRUD in [`lib/custom_agents.py`](/Users/ryanjohnson/Projects/writers-room/lib/custom_agents.py) and [`web/templates/agents.html`](/Users/ryanjohnson/Projects/writers-room/web/templates/agents.html)
- Automatic transcript saving for both CLI and web sessions into `transcripts/`
- Pytest suite covering agents, session orchestration, story state, custom agents, and the web API

## Quick Start

```bash
uv sync --group dev
cp .env.example .env
```

`uv` is now the canonical environment and dependency manager for this repo. `./start.sh`, `./start.sh --cli`, and `./start_web.sh` all prefer `uv` automatically when `pyproject.toml` is present.

If you need the legacy fallback path instead:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

If you also have the sibling `executive_reporting` repo checked out beside this project, you can enable the richer briefing component with:

```bash
uv pip install -r requirements-briefing.txt
```

Set `OPENROUTER_API_KEY` in `.env`. `OPENAI_API_KEY` and `ELEVENLABS_API_KEY` are only needed if you want experimental voice playback.

### Launch the Studio

```bash
./start.sh
```

### Run the CLI

```bash
./start.sh --cli
```

Or:

```bash
uv run python main.py
```

### Run the Web UI

```bash
./start_web.sh
```

Or:

```bash
uv run uvicorn web.app:app --reload --port 5001
```

Open [http://localhost:5001](http://localhost:5001).

When a web session finishes, the server stores both the plain transcript and an HTML brief. The latest brief is available at [http://localhost:5001/briefs/latest](http://localhost:5001/briefs/latest).

If you enable the final-draft pass for a web session, Writers Room now saves:

- `transcripts/{YYMMDD}_{title-name}_transcript.txt`
- `transcripts/{YYMMDD}_{title-name}_brief.html`
- `final/{YYMMDD}_{title-name}_final.md`
- `pipelines/{YYMMDD}_{title-name}/` — a directory of per-asset files:
  - `status.md` — editing steps + polish checklist (one structured JSON call)
  - `marketing/logline.md`
  - `marketing/back-cover.md`
  - `marketing/character-sheet.md`
  - `marketing/pull-quotes.md`
  - `marketing/cover-brief.md`
  - `marketing/social-teasers.md`
  - `marketing/newsletter.md`
  - `marketing/landing-page.md`
  - `index.md` — links to every artifact, marks anything that failed as `PENDING`
  - `.failures.json` — written only when one or more items failed; used by
    `--retry-pipeline` and removed automatically once every item succeeds

Each marketing asset is generated with its own model call so long-form copy
(back-cover blurb, landing page) gets the full token budget instead of
competing with short-form items. Marketing calls run in parallel batches of two
to stay under provider rate limits.

Web sessions generate the pipeline directory automatically. The CLI supports
two entry points into the same pipeline module:

```bash
# Full regenerate: status + all eight marketing assets
uv run python main.py --run-pipeline final/260409_the-closet_final.md

# Retry only the items recorded in pipelines/{YYMMDD}_{title-name}/.failures.json
uv run python main.py --retry-pipeline final/260409_the-closet_final.md
```

`--retry-pipeline` is a no-op when the manifest is missing or empty.
Both pipeline commands exit non-zero when any item remains pending in
`.failures.json`.

## Tests

```bash
uv run pytest -q
```

`pytest.ini` restricts discovery to the real `tests/` suite so the legacy manual verification scripts at repo root are not collected.

## Operational Notes

- The web server supports one active session at a time. Session state is held in-process in [`web/app.py`](/Users/ryanjohnson/Projects/writers-room/web/app.py).
- Voice playback is experimental. The UI labels it explicitly and disables the toggle when no provider is configured.
- The web client now reconnects its WebSocket automatically after disconnects, but missed events during downtime are not replayed.
- `dnd` mode disables custom agents for the run so the table stays coherent: one Dungeon Master plus the core writer roster as players.
- Historical phase/fix markdown files were archived to `docs/archive/` to keep the repo surface clean.

## Key Files

- [`main.py`](/Users/ryanjohnson/Projects/writers-room/main.py): CLI entrypoint
- [`start.sh`](/Users/ryanjohnson/Projects/writers-room/start.sh): default launcher for the web studio (`--cli` for terminal mode)
- [`start_web.sh`](/Users/ryanjohnson/Projects/writers-room/start_web.sh): `uv`-first web launcher with venv/pip fallback
- [`lib/agents.py`](/Users/ryanjohnson/Projects/writers-room/lib/agents.py): OpenRouter client and context trimming
- [`lib/session.py`](/Users/ryanjohnson/Projects/writers-room/lib/session.py): web session lifecycle, producer scoring, transcript persistence
- [`web/static/js/app.js`](/Users/ryanjohnson/Projects/writers-room/web/static/js/app.js): WebSocket client, UI event handling, audio queue
- [`tests/test_web_app.py`](/Users/ryanjohnson/Projects/writers-room/tests/test_web_app.py): API coverage for custom-agent CRUD
