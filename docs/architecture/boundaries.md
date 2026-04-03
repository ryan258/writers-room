# boundaries.md - Design By Contract

## 1. The Route Boundary
- **Input Contract:** FastAPI endpoints accept Pydantic request models for structured inputs.
- **Output Contract:** Routes return `TemplateResponse`, `JSONResponse`, or plain JSON-compatible dict payloads.
- **Constraint:** Route handlers may update the dedicated `current_session` record or delegate to manager objects, but story logic stays in `lib/`.

## 2. The `lib/` Boundary
- **Input Contract:** `lib/` functions accept primitive Python types or strictly typed data structures.
- **Output Contract:** Return structured data. NO UI formatting within `lib/`.
- **Constraint:** `lib/` MUST NOT import `main.py` or know about HTTP request lifecycle. 

## 3. The API Provider Boundary
- **Input Contract:** Construct provider-agnostic prompt models inside `lib/`.
- **Output Contract:** Wrap third-party network calls (e.g., OpenRouter via `openai`, OpenAI TTS, ElevenLabs) to catch native exceptions and surface normalized project errors.
- **Constraint:** Never hardcode LLM model names into the UI layer.

## 4. Subprocess Boundary
- **Rule:** Avoid external process executions if a native Python library exists (e.g., `zipfile` instead of calling `zip`).
- **Input/Output Contract:** If subprocesses exist, strictly enforce timeouts and parse standard out. Don't rely on shell execution unless necessary.
