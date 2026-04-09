# Writers Room — Happy Path

This is the canonical, no-surprises path from a fresh checkout to a finished
session and a saved transcript. If anything in this doc disagrees with the
code, the code wins — start with [`SETUP.md`](../SETUP.md),
[`web/app.py`](../web/app.py), and [`main.py`](../main.py).

The happy path assumes:

- macOS or Linux with `python3` available
- [`uv`](https://github.com/astral-sh/uv) installed (the canonical env manager
  for this repo — `requirements.txt` is the fallback)
- An OpenRouter API key with at least a small balance
- You want a normal, non-experimental run: no voice, no custom agents, no
  failure modes to debug

---

## 1. Clone and enter the repo

```bash
git clone <repo-url> writers-room
cd writers-room
```

## 2. Install dependencies

With `uv` (preferred):

```bash
uv sync
```

Fallback path without `uv`:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Configure your API key

```bash
cp .env.example .env
```

Then edit `.env` and set:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
```

That's the only required variable. Leave `OPENAI_API_KEY` and
`ELEVENLABS_API_KEY` blank — voice is experimental and not part of the
happy path.

## 4. Run the test suite

```bash
uv run pytest -q
```

A green run here means your environment is wired up correctly. If pytest
fails before you've changed anything, stop and fix that first — don't
proceed assuming it'll sort itself out.

## 5. Launch the studio

```bash
./start.sh
```

This boots the FastAPI + WebSocket web UI on
[http://localhost:5001](http://localhost:5001). The script:

1. Verifies `.env` exists (warns if not)
2. Hands off to `./start_web.sh`, which uses `uv run uvicorn web.app:app`

Open the URL in a browser. You should see the Writers Room landing page with
mode tiles (D&D, Fantasy, Horror, Literary, Noir, Sci-Fi, Comedy).

## 6. Start your first session

In the web UI:

1. Pick a mode — **Horror** is a good first run because the agent roster is
   well-tuned for it.
2. Paste a prompt. If you need one, grab Demo 1 from
   [`docs/demos.md`](demos.md).
3. Leave the defaults: `rounds=3`, `temperature=0.9`,
   `producer_enabled=true`, `fire_worst=false`, `voice_enabled=false`,
   `include_custom_agents=true`.
4. Click **Start**.

The orchestrator runs in a background thread. The browser receives live
events over `ws://localhost:5001/ws` as each agent contributes.

## 7. Watch the round play out

For a non-D&D mode, each round is:

1. **Story State update** — the Center Table is recomputed and broadcast.
2. **Agents write in turn** — Rod Serling, Stephen King, H.P. Lovecraft,
   Jorge Luis Borges, Robert Stack, RIP Tequila Bot, plus any active
   custom agents from `lib/custom_agents.py`.
3. **The Producer scores** — each agent gets a 1–10 with a one-line reason.
4. **Leaderboard updates** — visible in the UI sidebar.

For D&D mode the loop is different: a DM frames the scene, each player
declares an action in character, and the Producer is disabled by design
(see `web/app.py:238` for the override).

## 8. Read the result

When all rounds complete:

- The full transcript is written to `transcripts/session_<timestamp>.txt`
- A rendered HTML brief is written next to it and surfaced at
  `/briefs/latest`
- If you enabled **Produce final draft** before launching (non-D&D only),
  a synthesized short story is written to
  `transcripts/web_session_<timestamp>_final.md` and served at
  `/drafts/latest`. The same story is also embedded as the headline
  section of the HTML brief.
- The session orchestrator stays in memory so you can call
  `/api/continue` to extend it for more rounds without losing the Story
  State

In the UI, click **View Brief** to see the formatted recap, or open the
`transcripts/` directory directly.

## 9. (Optional) Continue the session

From the UI, click **Continue** and pick a new round count. Under the hood
this hits `POST /api/continue` and reuses the existing
`SessionOrchestrator`, so the Story State, character arcs, and tension
levels carry over. Lost WebSocket events are *not* replayed — that's a
known limitation, not a bug.

## 10. Shut down cleanly

`Ctrl+C` in the terminal running `start.sh`. The web server supports one
live session at a time via in-process global state, so there's nothing
external to clean up.

---

## Happy path, but on the CLI

If you'd rather drive the room from a terminal:

```bash
./start.sh --cli --mode horror --rounds 3
```

You'll be prompted for a prompt, then the round loop runs inline with
colorized output. Useful flags (see `main.py:492`):

| Flag | Default | Purpose |
|---|---|---|
| `-r, --rounds N` | prompts you | Number of rounds to run |
| `--mode MODE` | prompts you | One of the seven story modes |
| `-t, --temperature F` | `0.9` | Sampling temperature for all agents |
| `-m, --model NAME` | `DEFAULT_MODEL` | Override the OpenRouter model |
| `--no-producer` | off | Skip the Producer scoring pass |
| `--fire-worst` | off | Drop the lowest-scoring agent at the end |
| `--no-continue` | off | Exit cleanly instead of asking to continue |
| `--skip-validation` | off | Skip the API key check (faster startup) |

Transcripts land in the same `transcripts/` directory as the web flow.

---

## Happy path, but over HTTP

If you want to script sessions instead of clicking:

```bash
curl -X POST http://localhost:5001/api/start \
  -H "Content-Type: application/json" \
  -d @docs/demos.md   # or any single JSON block from that file
```

Then either open the web UI to watch it stream, or connect a WebSocket
client to `ws://localhost:5001/ws`. Poll `GET /api/status` for a synchronous
view of `active`, the current Story State, and the agent roster.

Every field accepted by `/api/start` is documented in
[`docs/demos.md`](demos.md), and each demo there is a complete payload you
can post directly.

---

## What "happy" rules out

The happy path deliberately avoids:

- **Voice / TTS** — `lib/voice.py` is best-effort and gated on provider
  keys. Treat it as experimental.
- **Custom agents** — the built-in roster is sufficient for a first run.
  Add custom agents from `/agents` once you've seen a clean session end-to-end.
- **D&D mode for your first run** — it's a different orchestration loop
  (no Producer, different prompt structure). Get a Horror session under
  your belt first.
- **Final draft synthesis on by default** — `produce_final_draft` is opt-in
  and costs an extra two Editor passes after the last round. The happy
  path leaves it off until you've seen a normal session land cleanly.
- **Multi-tenant use** — the server holds one live session in process
  global state. Don't expose it to more than one concurrent user.
- **Resuming over a server restart** — sessions are in-memory; restarting
  `start.sh` drops the orchestrator. Transcripts on disk still survive.

If anything off the happy path bites you, check
[`docs/architecture/`](architecture/) for the deeper context, or
[`AGENTS.md`](../AGENTS.md) for repo-wide review and GitNexus rules.
