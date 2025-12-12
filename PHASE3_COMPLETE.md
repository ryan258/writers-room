# Phase 3: The Producer Agent - Complete! 🎬

Phase 3 adds a seventh AI agent—**The Producer**—who acts as a snarky Hollywood executive judging the writers' performances after each round.

## New Features

### 1. The Producer Agent

A meta-judge that evaluates all six writers after each round:
- **Personality**: Snarky Hollywood executive with witty commentary
- **Role**: Judges creativity, relevance, and entertainment value
- **Output**: Scores each writer 1-10 with brief comments
- **Color**: Green terminal output

### 2. Scoring System

Real-time performance tracking:
- Each writer receives a score (1-10) from the Producer after every round
- Scores are accumulated across all rounds
- Average scores calculated and displayed

### 3. Leaderboard Display

After each round, see:
- Rankings with medals (🥇🥈🥉)
- Average score per writer
- Full score history (e.g., "7, 8, 9")

Example:
```
📊 LEADERBOARD - After Round 2
🥇 Stephen King: 8.5/10 avg (9, 8)
🥈 H.P. Lovecraft: 7.5/10 avg (7, 8)
🥉 Rod Serling: 7.0/10 avg (7, 7)
...
```

### 4. Winner Declaration

At the end of all rounds:
- Final leaderboard displayed
- Winner announced with fanfare
- Shows winning average score

### 5. Fire Worst Performer (Optional)

Use the `--fire-worst` flag to add drama:
- The lowest-scoring writer gets "fired" at the end
- Red-colored termination message
- Shows their poor average score

## CLI Usage

### Basic Usage (Producer Enabled by Default)
```bash
python main.py
```

The Producer will automatically judge after each round.

### Disable the Producer
```bash
python main.py --no-producer
```

Runs like Phase 2 (no judging, no scores).

### Fire the Worst Performer
```bash
python main.py --fire-worst
```

The Producer fires the lowest-scoring writer at the end.

### Combined Example
```bash
# Run 5 rounds with higher creativity and fire the worst
python main.py -r 5 -t 1.2 --fire-worst
```

## How It Works

1. **After Each Round**: Once all 6 writers have contributed, the Producer reviews the round
2. **Evaluation**: The Producer sees the prompt + the 6 recent contributions
3. **Scoring**: Producer outputs format like "Stephen King: 8/10 - Great horror atmosphere!"
4. **Parsing**: System extracts scores using regex pattern matching
5. **Leaderboard**: Rankings updated and displayed
6. **Final Results**: Winner declared and worst performer optionally fired

## Technical Details

### Producer Configuration

```python
# In personalities.py
PRODUCER = """You are The Producer, a snarky Hollywood executive judging a writers room. Review the recent contributions from each writer and provide:
1. Brief snarky commentary (2-3 sentences total)
2. Score each writer 1-10
3. Format: "Writer Name: X/10 - [comment]" for each

Be witty, harsh but fair. Focus on creativity, relevance to the prompt, and entertainment value."""
```

### Agent Parameters

The Producer uses different parameters than the writers:
- **temperature**: 0.7 (lower for consistent judging)
- **max_tokens**: 300 (needs space to evaluate 6 agents)

Regular writers use:
- **temperature**: 0.9 (default, configurable via `-t`)
- **max_tokens**: 80 (one sentence only)

### Score Parsing

The system looks for patterns like:
- `Rod Serling: 8/10 - Great twist!`
- `Stephen King: 7 / 10 - Too predictable`

Scores are clamped to 1-10 range.

## Examples

### Producer's Typical Response

```
Rod Serling: 7/10 - Solid ironic twist, but a bit predictable.
Stephen King: 9/10 - Chilling character work, nailed the atmosphere.
H.P. Lovecraft: 6/10 - Too much purple prose, not enough action.
Jorge Luis Borges: 8/10 - Clever paradox, though maybe too intellectual.
Robert Stack: 7/10 - Good mystery setup, classic Stack energy.
RIP Tequila Bot: 4/10 - Shameless product placement ruined the mood.
```

### Leaderboard Output

```
📊 LEADERBOARD - After Round 3
🥇 Stephen King: 8.7/10 avg (9, 8, 9)
🥈 Jorge Luis Borges: 7.7/10 avg (8, 7, 8)
🥉 Rod Serling: 7.3/10 avg (7, 7, 8)
4. H.P. Lovecraft: 6.7/10 avg (6, 7, 7)
5. Robert Stack: 6.3/10 avg (7, 6, 6)
6. RIP Tequila Bot: 4.3/10 avg (4, 5, 4)
```

### Winner Declaration

```
🏆 ============================================================
   WINNER: Stephen King with 8.7/10 average!
============================================================
```

### Fire Worst Performer

```
🔥 ============================================================
   RIP Tequila Bot has been FIRED!
   (Lowest score: 4.3/10)
============================================================
```

## Architecture Notes

### New Functions

- `parse_producer_scores(response, agent_names)`: Extracts scores from Producer text
- `display_leaderboard(agent_scores, round_num)`: Shows rankings and medals

### Score Tracking

```python
agent_scores = {
    "Rod Serling": [7, 7, 8],      # List of scores per round
    "Stephen King": [9, 8, 9],
    # ... etc
}
```

### Context for Producer

The Producer sees:
- The original user prompt
- The last 6 messages (the current round's contributions)

This keeps token usage manageable while giving enough context to judge.

## Token Impact

### Per Round with Producer:
- 6 writers × 80 tokens = 480 tokens
- Producer evaluation: ~300 tokens
- Total: ~780 tokens/round

### Compared to Phase 2:
- Phase 2: ~480 tokens/round
- Phase 3: ~780 tokens/round
- Increase: +62% per round

Still very efficient! A 3-round session costs ~2,400 tokens (~$0.02-$0.03).

## Compatibility

- Works with all Phase 2 features (rounds, continue, temperature, model override)
- Can be disabled with `--no-producer` for classic Phase 2 behavior
- Safe parsing: Missing scores won't crash the system

## What's Next?

Now that we have judging and scoring, possible future enhancements:
- **Phase 4**: Add TTS so you can hear the Producer's snarky commentary
- **Phase 5**: Web interface with visual leaderboard
- **Future**: Producer could provide specific feedback prompts for next round

---

**Status**: Phase 3 Complete ✅
**Date**: 2024-12-12
**Features**: Producer agent, scoring system, leaderboards, winner declaration, fire worst performer
