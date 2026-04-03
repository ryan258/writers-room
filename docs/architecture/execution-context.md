# execution-context.md - Pragmatic Paranoia

## 1. Fail Fast, Log Loudly
- **Rule:** Unhandled exceptions must crash the application during instantiation, but must never crash the server loop.
- **Constraint:** All external network/DB calls MUST be guarded by explicit `try/except` blocks handling `httpx.RequestError` or `Timeout`.

## 2. Default-Deny Error Responses
- **Rule:** Exceptions inside route handlers must be caught by a centralized FastAPI exception handler.
- **Constraint:** DO NOT leak stack traces to the UI. Return standardized HTMX error fragments or JSON error shapes with generic failure context.

## 3. Defensive Configuration
- **Rule:** Validate required configuration before starting a writing session.
- **Constraint:** `OPENROUTER_API_KEY` is required for text generation. `OPENAI_API_KEY` and `ELEVENLABS_API_KEY` should gate only experimental voice features, not the whole app.

## 4. Input Sanitization
- **Rule:** Assume all client HTMX payloads are malicious or malformed.
- **Constraint:** Validate all input length, schema, and types before allowing it to touch the `lib/` boundary.

## 5. Predictable Timeout Policies
- **Rule:** No infinite hanging processes. 
- **Constraint:** All client timeouts must be strictly defined (e.g., 10s for LLM inference, 2s for local TTS generation). Warn users immediately if exceeded.
