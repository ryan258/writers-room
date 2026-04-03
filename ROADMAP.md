# Writers Room Roadmap

## Current State

Writers Room is shippable in its current form:

- CLI and web UI are both operational
- Custom agents support create, edit, delete, and active/inactive toggling
- Web sessions now save transcripts to `transcripts/`
- A real pytest suite covers the core library and API paths
- Setup and assistant-facing docs now match the codebase

## In Scope for the Current Release

- Collaborative writing rounds with six built-in writers
- Producer scoring and leaderboard updates
- Six genre modes
- Shared Center Table story-state management
- Custom agent management
- Best-effort experimental voice playback

## Post-Ship Enhancements

- Configurable built-in roster from the web UI
- Replay or recovery for WebSocket events missed during reconnects
- Stronger end-to-end coverage for live TTS providers
- Additional interaction modes beyond the current collaboration-first behavior

## Release Constraints

- The web server is single-session by design today
- Voice remains experimental until provider-level live verification is automated
