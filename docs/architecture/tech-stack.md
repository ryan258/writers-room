# tech-stack.md - Environment Limits & Constraints

## 1. Permitted Stack
- **Language:** Python 3.10+
- **Backend:** FastAPI, Uvicorn
- **Templating/UI:** Jinja2 templates plus vanilla JavaScript and native WebSockets. No JS frameworks.
- **Styling:** Vanilla CSS using the Candlelight palette.
- **Persistence:** Local JSON/text files for agents and transcripts.
- **LLM Integrations:** `openai` >= 1.0.0 against the OpenRouter API
- **Optional Voice:** OpenAI TTS, ElevenLabs, or `pyttsx3`

## 2. Forbidden Stack
- ❌ Docker / Kubernetes
- ❌ Node.js, `package.json`, Webpack
- ❌ React, Vue, Angular
- ❌ Microservices (Must be Monolith)
- ❌ Complex Auth (OAuth/JWT/User Accounts)

## 3. Versioning Constraints
- Dependency definitions live exactly in `requirements.txt`.
- No strict version pinning across all packages unless patching a 0-day; instead prefer standard range minimums logic (e.g., `>=`).

## 4. Environment Variables
- Session execution requires `OPENROUTER_API_KEY`.
- `OPENAI_API_KEY` and `ELEVENLABS_API_KEY` are optional and only needed for experimental voice playback.

## 5. Operation constraints
- **Environment:** Bare metal macOS execution. 
- **Shell:** Scripts use `#!/bin/bash` or `zsh` constraints.
- **Port:** The bundled web launcher serves on port `5001`.
