# Changelog

All notable changes to this project will be documented in this file.

## [Phase 3.0] - 2024-12-12

### Added - The Producer Agent
- **The Producer**: Seventh AI agent that judges all writers after each round
  - Snarky Hollywood executive personality
  - Provides commentary and scores (1-10) for each writer
  - Uses 300 max_tokens vs. 80 for regular writers
  - Lower temperature (0.7) for consistent judging
- **Scoring System**: Tracks performance across all rounds
  - Parses scores from Producer's responses using regex
  - Stores scores per agent in dictionary
  - Calculates averages automatically
- **Leaderboard Display**: Shows rankings after each round
  - Medals for top 3 (🥇🥈🥉)
  - Average scores and score history
  - Color-coded in green
- **Winner Declaration**: Final results at end of session
  - Final leaderboard display
  - Winner announcement with fanfare
- **Fire Worst Performer**: Optional dramatic ending
  - `--fire-worst` CLI flag
  - Terminates lowest-scoring writer
  - Red-colored "FIRED" message
- **CLI Flags**:
  - `--no-producer`: Disable Producer for Phase 2 behavior
  - `--fire-worst`: Fire the worst performer at end
- **Agent Class Enhancement**: Added `max_tokens` parameter
  - Default 80 for writers (one sentence)
  - 300 for Producer (needs to evaluate 6 agents)

### Added - Documentation
- `PHASE3_COMPLETE.md`: Full Phase 3 feature documentation
- Updated `README.md` with Phase 3 features
- Updated `ROADMAP.md` to mark Phase 3 complete

### Fixed - Critical Bugs
- **Context Window**: Now preserves original user prompt across all rounds
  - Previous bug: After round 1 (6 agent responses), the sliding window of 5 messages would drop the original prompt
  - Fix: Always keep first message (user prompt) + last 4 messages
  - Impact: Agents no longer drift off-topic in later rounds
- **System Role**: Moved personality instructions from user role to system role
  - Previous bug: Personality sent as user message, creating two consecutive user messages
  - Fix: Use proper system role for personality instructions
  - Impact: Better model compliance with personality constraints
- **API Validation**: Improved error handling
  - Previous bug: Network errors returned "valid" and failed later
  - Fix: Detect and report specific error types (timeout, 404, network)
  - Impact: Clearer error messages during startup
- **Documentation**: Fixed inaccuracies in README
  - Removed references to non-existent `web/` folder
  - Corrected model name (mistralai/ministral-3b-2512)
  - Fixed agent count (6 writers, not 5)
- **Code Cleanup**: Removed duplicate comment lines in `personalities.py`

## [Phase 2.0] - 2024-12-12

### Added - Enhanced Experience
- **Configurable Rounds**: User prompt or CLI arg (`-r/--rounds`) to set number of rounds
- **Continue Option**: After rounds complete, option to continue with more rounds
  - Can specify exact number (e.g., "3") or use y/n
  - Disable with `--no-continue` flag
- **API Key Validation**: Tests API key on startup
  - Validates format (must start with `sk-or-`)
  - Makes test API call to verify key works
  - Detects invalid keys, rate limits, expired keys
  - Skip with `--skip-validation` for faster startup
- **Model Override**: CLI arg (`-m/--model`) to use custom model for all agents
- **Temperature Control**: CLI arg (`-t/--temperature`) to adjust creativity (0.0-2.0)
- **Help Text**: `--help` shows all available options

### Changed
- Agent class now accepts `temperature` parameter
- Better error messages throughout
- Main function now uses argparse for CLI arguments

## [Phase 1.4] - 2024-12-12

### Fixed - CRITICAL: Echo Problem (Fix V2)
- **The Problem**: V1.3 didn't work - models were echoing context instead of adding new sentences
- **New approach**: Nuclear option to eliminate echoing
  - **System prompts**: Now lead with "OUTPUT ONLY YOUR NEW SENTENCE. Do not repeat..."
  - **Context window**: Reduced to 5 messages (down from 8)
  - **Message truncation**: Reduced to 200 chars (down from 400)
  - **max_tokens**: Reduced to 80 (down from 120)
  - **presence_penalty**: Increased to 1.2 (up from 0.6) - maximum strength
  - **frequency_penalty**: Added at 1.0 to penalize repeated tokens
  - **Post-processing**: Added echo detection and removal
- **Expected result**: ~6,300 tokens/session (vs. original 156k = 96% reduction)

## [Phase 1.3] - 2024-12-11

### Fixed - Token Optimization (V1 - DIDN'T WORK)
- Attempted to reduce tokens but models still echoed context
- See Phase 1.4 for actual fix

### Changed
- All personality prompts now ultra-concise for token efficiency
- Switched model from `nvidia/nemotron` to `mistralai/ministral-3b-2512`

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
