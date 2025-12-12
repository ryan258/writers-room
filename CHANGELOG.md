# Changelog

All notable changes to this project will be documented in this file.

## [Phase 1.2] - 2024-12-11

### Changed
- **Writers Room Roster**: Replaced sitcom writer with five legendary authors
  - Removed: Bob the Hack (Sitcom Writer)
  - Added: Rod Serling, Stephen King, H.P. Lovecraft, Jorge Luis Borges, Robert Stack
  - Now features 6 agents total (5 legendary writers + RIP Tequila Bot)
- Updated all agents to use `moonshotai/kimi-k2:free` model
- New color scheme for 6 agents (Cyan, Red, Magenta, Blue, White, Yellow)
- Updated example prompts to better suit the new writer personalities

## [Phase 1.1] - 2024-12-11

### Fixed
- **Bug**: Fixed `FileNotFoundError` when `transcripts/` directory doesn't exist on fresh clone
  - Added `os.makedirs(os.path.dirname(filename), exist_ok=True)` in `save_transcript()` function
  - Directory is now created automatically before saving transcripts

## [Phase 1.0] - 2024-12-11

### Added
- Initial MVP implementation
- Agent class with OpenRouter integration
- Three personality system prompts (Cosmic Horror, Sitcom, Marketing)
- Main orchestrator with round-robin conversation loop
- Colored terminal output (green, purple, yellow)
- Automatic transcript saving
- Error handling for missing API keys
- Setup documentation
