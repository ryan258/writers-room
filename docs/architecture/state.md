# state.md - Session and Persistence Rules

## 1. Web Session State
- **Rule:** The web server keeps one in-process session record in `web/app.py`.
- **Constraint:** `current_session` and `app.state.loop` are process-local. They support one active session and do not survive restarts.

## 2. Runtime Ownership
- **Rule:** `web/app.py` owns websocket connections and session lifecycle. `lib/session.py` owns conversation history, scoring, and transcript assembly.
- **Constraint:** Route handlers should coordinate the session, not implement story logic themselves.

## 3. Persistent Outputs
- **Rule:** Durable state is file-based.
- **Constraint:** Custom agents are stored in `agents/`, transcripts in `transcripts/`, and one-off historical notes belong in `docs/archive/`.

## 4. Mutation Locality
- **Rule:** Each module owns one slice of mutable state.
- **Constraint:** `lib/story_state.py` mutates story progression, `lib/session.py` mutates session transcripts and scores, and `web/app.py` mutates connection/session metadata.

## 5. Restart Semantics
- **Rule:** In-memory state is disposable.
- **Constraint:** Features that need recovery after a process restart must add explicit persistence rather than extending module-level globals.
