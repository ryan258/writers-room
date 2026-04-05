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

Launch the studio app:

```bash
./start.sh
```

Run the CLI explicitly:

```bash
./start.sh --cli
```

Run the web UI:

```bash
./start_web.sh
```

Run tests:

```bash
uv run pytest -q
```

Direct entrypoints:

```bash
uv run python main.py --help
uv run uvicorn web.app:app --reload --port 5001
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

- `uv` is the canonical environment/dependency manager for this repo; `requirements.txt` is only the fallback path for non-`uv` installs
- The web server supports one live session at a time via in-process global state
- WebSocket reconnect is automatic, but lost events are not replayed
- Web and CLI transcripts are written to `transcripts/`
- See [`AGENTS.md`](/Users/ryanjohnson/Projects/writers-room/AGENTS.md) for repo-wide review and GitNexus rules

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **writers-room** (803 symbols, 1721 relationships, 54 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/writers-room/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/writers-room/context` | Codebase overview, check index freshness |
| `gitnexus://repo/writers-room/clusters` | All functional areas |
| `gitnexus://repo/writers-room/processes` | All execution flows |
| `gitnexus://repo/writers-room/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
