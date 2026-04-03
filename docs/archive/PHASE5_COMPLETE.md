# Phase 5: Dark-Themed Web Interface - Complete! 🌐

Phase 5 delivers a beautiful, dark-themed web interface with real-time agent collaboration, live leaderboards, and smooth animations.

## Features Overview

### 1. **Dark-Themed UI**
- Sleek black and dark purple gradient background
- Color-coded agent cards matching their terminal colors
- Smooth animations and transitions
- Fully responsive design

### 2. **Real-Time Agent Streaming**
- Live WebSocket connections via Socket.IO
- Agents appear to "think" with pulsing animations
- Responses stream in real-time to individual agent cards
- Scroll animations and visual feedback

### 3. **Live Leaderboards**
- Updates automatically after Producer evaluations
- Medals for top 3 performers (🥇🥈🥉)
- Shows average scores and full score history
- Smooth transitions and hover effects

### 4. **Configuration Panel**
- Story prompt input with multi-line textarea
- Adjustable rounds (1-10)
- Temperature control (0.0-2.0)
- Producer enable/disable toggle
- Fire worst performer option

### 5. **Status Tracking**
- Active session banner with current status
- Real-time updates ("Round 2 of 3", "Producer judging...")
- Winner and loser announcements with dramatic styling

### 6. **Agent Cards**
Six legendary writers plus The Producer:
- **Rod Serling** (Cyan) - Twilight Zone irony
- **Stephen King** (Red) - Character horror
- **H.P. Lovecraft** (Magenta) - Cosmic dread
- **Jorge Luis Borges** (Blue) - Philosophical paradoxes
- **Robert Stack** (White) - Mystery questions
- **RIP Tequila Bot** (Yellow) - Shameless marketing
- **The Producer** (Green) - Snarky judge

## Installation & Setup

### 1. Install Web Dependencies

```bash
# Make sure you're in your virtual environment
source venv/bin/activate  # Mac/Linux
# OR: venv\Scripts\activate  # Windows

# Install all dependencies including web interface
pip install -r requirements.txt
```

### 2. Start the Web Server

```bash
# From the project root directory
cd web
python app.py
```

You should see:
```
🌐 Starting Writers Room Web Interface...
📍 Navigate to: http://localhost:5000
🎬 Press Ctrl+C to stop
```

### 3. Open in Browser

Navigate to **http://localhost:5000** in your web browser.

**Recommended browsers**: Chrome, Firefox, Edge, Safari (latest versions)

## Usage Guide

### Starting a Session

1. **Enter Story Prompt**
   - Type your creative prompt in the text area
   - Example: "A detective discovers a conspiracy involving time travel"

2. **Configure Settings**
   - **Rounds**: Number of rounds (1-10, default: 3)
   - **Creativity**: Temperature setting (0.0-2.0, default: 0.9)
   - **Enable Producer**: Check to enable judging and scoring
   - **Fire Worst**: Check to fire the lowest scorer at the end

3. **Click "Start Writers Room"**
   - Button will show spinner while initializing
   - Session begins automatically

### Watching the Session

1. **Status Banner**: Shows current round and activity
2. **Agent Cards**: Watch agents "think" (pulsing animation) then display responses
3. **Leaderboard**: Appears after each round if Producer is enabled
4. **Final Results**: Winner banner and optional "fired" banner at completion

### After Completion

- Review all agent responses in their cards
- Check final leaderboard rankings
- See winner announcement
- Start a new session with different prompts

## Architecture

### Backend (Flask + SocketIO)

**File**: `web/app.py`

- **Flask** web server on port 5000
- **SocketIO** for real-time WebSocket communication
- **Threading** for background session execution
- **API endpoints**:
  - `GET /` - Main UI page
  - `POST /api/start` - Start new session
  - `GET /api/status` - Get session status

**WebSocket Events** (Server → Client):
- `connected` - Acknowledgment of connection
- `session_started` - Session initialization complete
- `round_started` - New round beginning
- `agent_thinking` - Agent is generating response
- `agent_response` - Agent completed response
- `producer_thinking` - Producer evaluating
- `producer_verdict` - Producer scores released
- `round_completed` - Round finished
- `session_completed` - All rounds done
- `error` - Error occurred

### Frontend (HTML + CSS + JavaScript)

**Files**:
- `web/templates/index.html` - Main UI structure
- `web/static/css/style.css` - Dark theme styling
- `web/static/js/app.js` - WebSocket client and UI logic

**Key Features**:
- Socket.IO client library (CDN)
- Event-driven UI updates
- Smooth animations via CSS
- Responsive grid layout

### File Structure

```
web/
├── app.py                 # Flask backend
├── static/
│   ├── css/
│   │   └── style.css      # Dark theme
│   └── js/
│       └── app.js         # Client logic
└── templates/
    └── index.html         # Main UI
```

## Technical Details

### Real-Time Communication Flow

1. **Client connects** → Server acknowledges
2. **User starts session** → POST to `/api/start`
3. **Server initializes** → Emits `session_started`
4. **For each agent**:
   - Server emits `agent_thinking`
   - Agent generates response
   - Server emits `agent_response`
5. **After round completes**:
   - Server emits `producer_thinking`
   - Producer evaluates
   - Server emits `producer_verdict` with leaderboard
6. **After all rounds** → Server emits `session_completed`

### Color Scheme

```css
--bg-primary: #0f0f0f       /* Main background */
--bg-secondary: #1a1a1a     /* Cards */
--bg-tertiary: #252525      /* Response items */
--text-primary: #ffffff     /* Main text */
--text-secondary: #b0b0b0   /* Secondary text */
--accent-cyan: #00ffff      /* Rod Serling */
--accent-green: #00ff00     /* Producer */
--accent-red: #ff0000       /* Stephen King */
```

### Animations

- **Pulsing glow**: Agent cards while thinking
- **Slide in**: New responses appearing
- **Winner glow**: Winner banner pulsing green
- **Spinner**: Loading states

### Responsive Breakpoints

- **Desktop**: 1400px max width, 2-3 column grid
- **Tablet**: Auto-fit grid, minimum 350px cards
- **Mobile** (<768px): Single column layout

## Performance Considerations

### Token Usage (Same as CLI)
- Writers: 80 tokens each × 6 = 480 tokens/round
- Producer: 300 tokens/evaluation
- **Total per round**: ~780 tokens
- **3-round session**: ~2,400 tokens (~$0.02-$0.03)

### Network
- WebSocket maintains single persistent connection
- Minimal data transfer (text responses only)
- No heavy assets (CSS/JS are lightweight)

### Browser Compatibility
- Modern browsers with WebSocket support required
- Tested on Chrome 120+, Firefox 120+, Safari 17+

## Troubleshooting

### "Connection Failed"
- Ensure web server is running (`python web/app.py`)
- Check port 5000 is not in use
- Verify firewall settings

### "Session Already Active"
- Wait for current session to complete
- Refresh page to reset state

### Agents Not Responding
- Check `.env` file has valid `OPENROUTER_API_KEY`
- Verify internet connection
- Check browser console for errors (F12)

### Leaderboard Not Showing
- Ensure "Enable Producer" is checked
- Producer must successfully parse scores from responses
- Check browser console for parsing errors

## Comparison: CLI vs Web Interface

| Feature | CLI | Web Interface |
|---------|-----|---------------|
| Real-time updates | ✓ | ✓ |
| Agent responses | Sequential | Parallel display |
| Leaderboard | Text-based | Visual with medals |
| Configuration | CLI flags | Form inputs |
| Accessibility | Terminal required | Browser-based |
| Aesthetics | Colored text | Dark theme UI |
| Multi-user | ✗ | Potentially (with auth) |

Both interfaces use the same backend logic (agents.py, personalities.py).

## Future Enhancements

Potential additions for Phase 5.x:

- **User Authentication**: Multi-user sessions
- **Session History**: Save and replay past sessions
- **Custom Agents**: UI for creating new personalities
- **Audio Playback**: TTS integration (Phase 4)
- **Mobile App**: Native mobile wrapper
- **Export**: Download transcripts as PDF/TXT
- **Themes**: Light mode, custom color schemes

## Examples

### Starting a Horror Story

**Prompt**: "A family moves into a house where the previous owners disappeared"

**Configuration**:
- Rounds: 3
- Temperature: 1.1 (high creativity)
- Producer: Enabled
- Fire Worst: Enabled

**Expected Flow**:
1. Status: "Round 1 of 3"
2. Rod Serling adds ironic twist
3. Stephen King develops character horror
4. H.P. Lovecraft introduces cosmic elements
5. Jorge Borges creates paradox
6. Robert Stack poses mystery
7. RIP Tequila Bot... markets tequila
8. Producer judges and scores
9. Leaderboard updates
10. Repeat for rounds 2-3
11. Winner declared
12. Worst performer fired (if enabled)

### Quick Test

**Prompt**: "A programmer discovers their code is alive"

**Configuration**:
- Rounds: 1
- Temperature: 0.9
- Producer: Enabled
- Fire Worst: Disabled

Perfect for quick testing!

## Development Notes

### Adding New Agents

1. Add personality to `personalities.py`
2. Update `agent_configs` in `web/app.py`
3. Add agent card to `web/templates/index.html`
4. Add styles to `web/static/css/style.css`
5. Update `agentIds` in `web/static/js/app.js`

### Customizing Theme

Edit `web/static/css/style.css`:
- Change `:root` CSS variables for colors
- Modify gradient in `body` for background
- Adjust animation timings

### Debugging

**Backend logs**: Terminal running `python web/app.py`

**Frontend logs**: Browser Developer Tools (F12) → Console

**Network**: Browser Dev Tools → Network tab → WS (WebSocket)

---

**Status**: Phase 5 Complete ✅
**Date**: 2024-12-12
**Features**: Dark theme UI, real-time streaming, live leaderboards, WebSocket communication
**Next**: Phase 4 (Audio/TTS) or Phase 6 (Custom agents & story modes)
