# Writers Room Web Interface

Dark-themed web UI with real-time agent collaboration and live leaderboards.

## Quick Start

### 1. Install Dependencies

```bash
# From project root
pip install -r requirements.txt
```

### 2. Set Up Environment

Make sure your `.env` file in the project root has:
```
OPENROUTER_API_KEY=sk-or-v1-your-key-here
YOUR_SITE_URL=http://localhost
YOUR_SITE_NAME=WritersRoomWeb
```

### 3. Start the Server

```bash
# From project root
uvicorn web.app:app --reload --port 5001
```

### 4. Open in Browser

Navigate to: **http://localhost:5001**

## Features

- 🎨 **Dark Theme**: Beautiful gradient background with agent cards
- ⚡ **Real-Time**: WebSocket streaming of agent responses
- 📊 **Live Leaderboards**: See rankings update after each round
- 🎬 **The Producer**: Optional judge with snarky commentary
- 🔥 **Fire Worst**: Optional dramatic ending
- 📱 **Responsive**: Works on desktop, tablet, and mobile

## Usage

1. Enter a story prompt
2. Configure rounds, temperature, and Producer options
3. Click "Start Writers Room"
4. Watch agents collaborate in real-time!

## Architecture

- **Backend**: FastAPI + native WebSocket
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Real-Time**: WebSocket for live updates
- **Styling**: CSS custom properties, dark theme

## Files

- `web/app.py` - FastAPI backend with WebSocket handlers
- `templates/index.html` - Main UI structure
- `static/css/style.css` - Dark theme styling
- `static/js/app.js` - Client-side WebSocket logic

## Troubleshooting

**Connection Failed?**
- Make sure server is running: `uvicorn web.app:app --reload --port 5001`
- Check port 5001 is available
- Verify firewall settings

**No Responses?**
- Check `.env` has valid `OPENROUTER_API_KEY`
- Verify internet connection
- Check browser console (F12) for errors

## Documentation

See `../PHASE5_COMPLETE.md` for comprehensive documentation.

## Development

**Run in Debug Mode:**
```bash
uvicorn web.app:app --reload --port 5001
```

**Custom Port:**
Pass a different `--port` to uvicorn.

---

For more information, see the main project README and PHASE5_COMPLETE.md.
