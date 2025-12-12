# Quick Setup Guide

## Phase 1 MVP - Ready to Run!

### Step 1: Set up your environment

```bash
# Create a virtual environment
python3 -m venv venv

# Activate it (macOS/Linux)
source venv/bin/activate

# Activate it (Windows)
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure OpenRouter API

1. Get your API key from [OpenRouter](https://openrouter.ai/)
2. Copy the example env file:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your API key:
   ```
   OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
   YOUR_SITE_URL=http://localhost
   YOUR_SITE_NAME=AgentSwarmLocal
   ```

### Step 3: Run the Writers Room!

**Basic usage:**
```bash
python main.py
```

**With options (Phase 2):**
```bash
# Specify number of rounds
python main.py -r 5

# Use a different model
python main.py -m "mistralai/mistral-7b-instruct"

# Adjust creativity (temperature)
python main.py -t 1.5  # More creative
python main.py -t 0.3  # More focused

# Quick session (no continue prompt)
python main.py -r 3 --no-continue

# See all options
python main.py --help
```

## What to Expect

- You'll be prompted to enter a story idea
- Six legendary AI agents will collaborate (argue) for 3 rounds:
  - **Rod Serling** (Cyan) - Twilight Zone creator, master of ironic twists
  - **Stephen King** (Red) - Character-driven horror specialist
  - **H.P. Lovecraft** (Magenta) - Cosmic horror and forbidden knowledge
  - **Jorge Luis Borges** (Blue) - Philosophical metafiction and labyrinths
  - **Robert Stack** (White) - Unsolved Mysteries dramatic narrator
  - **RIP Tequila Bot** (Yellow) - Aggressive marketing executive
- Each session saves a transcript to `transcripts/` (directory created automatically)

## Example Prompts to Try

- "A man discovers a mysterious door in his basement."
- "Someone receives a phone call from their future self."
- "A small town librarian finds a book that shouldn't exist."
- "A detective investigates a case where all the witnesses tell different stories."
- "An ordinary person wakes up in a room with no memory of how they got there."

## Troubleshooting

**No colored output on Windows?**
- Colorama should handle this, but if it doesn't work, try Windows Terminal instead of CMD

**API errors?**
- Check your `.env` file has the correct API key
- Verify your OpenRouter account has credits
- Some models may not be available - you can edit `personalities.py` to change models

**Responses are too long/short?**
- Edit `max_tokens` in `agents.py` (currently 300)
- Adjust the system prompts in `personalities.py`

## Next Steps

Once this works, you can:
- Try different models in `personalities.py`
- Adjust agent personalities
- Change the number of rounds in `main.py`
- Move to Phase 2 of the roadmap (enhanced features)
