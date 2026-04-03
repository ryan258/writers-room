#!/usr/bin/env python3
"""
Writers Room Web Interface
FastAPI backend for real-time collaborative storytelling.
"""

import asyncio
import os
import sys
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add repo root to path for lib imports
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from lib.custom_agents import CustomAgentManager, CustomAgent, list_templates
from lib.personalities import STORY_MODES, DEFAULT_MODEL
from lib.session import SessionOrchestrator, SessionEvent
from lib.voice import get_voice_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.loop = asyncio.get_running_loop()
    yield


app = FastAPI(lifespan=lifespan)

# Static files and templates
WEB_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))

# CORS configuration
origins_env = os.getenv("CORS_ORIGINS", "*")
origins = [o.strip() for o in origins_env.split(",") if o.strip()] if origins_env else ["*"]
allow_all = "*" in origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else origins,
    allow_credentials=False if allow_all else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global session state
current_session: Dict[str, Any] = {
    "orchestrator": None,
    "thread": None,
    "active": False,
    "last_transcript": None,
}

# Custom agent manager
custom_agent_manager = CustomAgentManager()


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send(self, websocket: WebSocket, event: str, data: Dict[str, Any]) -> None:
        await websocket.send_json({"event": event, "data": data})

    async def broadcast(self, event: str, data: Dict[str, Any]) -> None:
        if not self.active_connections:
            return
        message = {"event": event, "data": data}
        stale: List[WebSocket] = []
        for ws in list(self.active_connections):
            try:
                await ws.send_json(message)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(ws)


manager = ConnectionManager()


def emit_event(event: str, data: Dict[str, Any]) -> None:
    """Thread-safe event emitter for SessionOrchestrator."""
    loop = getattr(app.state, "loop", None)
    if loop:
        asyncio.run_coroutine_threadsafe(manager.broadcast(event, data), loop)


def run_session_thread(prompt: str, rounds: int, config: Dict[str, Any]) -> None:
    global current_session
    try:
        current_session["active"] = True
        current_session["last_transcript"] = None
        orchestrator = SessionOrchestrator(emit_event)
        current_session["orchestrator"] = orchestrator

        orchestrator.initialize(prompt, config)
        orchestrator.run_session(rounds)
        current_session["last_transcript"] = orchestrator.transcript_path
    except Exception as exc:
        emit_event(SessionEvent.ERROR, {"message": str(exc)})
    finally:
        current_session["active"] = False


class StartRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    rounds: int = Field(3, ge=1, le=10)
    temperature: float = Field(0.9, ge=0, le=2)
    producer_enabled: bool = True
    fire_worst: bool = False
    mode: str = "horror"
    voice_enabled: bool = False
    include_custom_agents: bool = True
    model: Optional[str] = None


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1)
    specialty: str = Field(..., min_length=1)
    guidance: Optional[str] = ""
    voice_id: Optional[str] = "alloy"
    color: Optional[str] = "#888888"
    avatar_emoji: Optional[str] = "pen"


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    specialty: Optional[str] = None
    guidance: Optional[str] = None
    voice_id: Optional[str] = None
    color: Optional[str] = None
    avatar_emoji: Optional[str] = None
    is_active: Optional[bool] = None


# =============================================================================
# ROUTES
# =============================================================================

@app.get("/")
async def index(request: Request):
    """Render the main UI."""
    return templates.TemplateResponse("index.html", {"request": request, "modes": STORY_MODES})


@app.get("/agents")
async def agents_page(request: Request):
    """Render the custom agents UI."""
    return templates.TemplateResponse("agents.html", {"request": request})


@app.post("/api/start")
async def start_session(req: StartRequest):
    """Start a new writers room session."""
    if current_session.get("active"):
        return JSONResponse({"error": "Session already active"}, status_code=400)

    prompt = req.prompt.strip()
    if not prompt:
        return JSONResponse({"error": "Prompt is required"}, status_code=400)

    config = req.model_dump()
    config["model"] = req.model or DEFAULT_MODEL
    config["prompt"] = prompt

    # Start session in background thread
    thread = threading.Thread(
        target=run_session_thread,
        args=(prompt, req.rounds, config),
        daemon=True,
    )
    thread.start()
    current_session["thread"] = thread

    return {"status": "started"}


@app.get("/api/status")
async def get_status():
    """Get current session status."""
    story_state = None
    config = {}

    orch = current_session.get("orchestrator")
    if orch and orch.active:
        if orch.story_manager:
            story_state = orch.story_manager.get_state().to_dict()
        config = orch.config

    return {
        "active": current_session.get("active", False),
        "config": config,
        "story_state": story_state,
        "last_transcript": current_session.get("last_transcript"),
    }


@app.get("/api/modes")
async def get_modes():
    """Get available story modes."""
    return STORY_MODES


@app.get("/api/voice/available")
async def check_voice_available():
    """Check if voice/TTS is available."""
    providers = []
    vm = get_voice_manager()
    providers = [p.value for p in vm.get_available_providers()] if vm else []

    return {
        "available": len(providers) > 0,
        "providers": providers,
        "experimental": True,
        "message": "Voice playback is experimental and currently best-effort only.",
    }


# =============================================================================
# CUSTOM AGENT API
# =============================================================================

@app.get("/api/agents")
async def list_custom_agents():
    """List all custom agents."""
    agents = custom_agent_manager.list_agents()
    return {"agents": [a.to_dict() for a in agents]}


@app.post("/api/agents")
async def create_custom_agent(payload: AgentCreate):
    """Create a new custom agent."""
    agent = CustomAgent(
        id="",
        name=payload.name,
        specialty=payload.specialty,
        guidance=payload.guidance or "",
        voice_id=payload.voice_id or "alloy",
        color=payload.color or "#888888",
        avatar_emoji=payload.avatar_emoji or "pen",
    )

    filepath = custom_agent_manager.save_agent(agent)

    return {
        "status": "created",
        "agent": agent.to_dict(),
        "filepath": filepath,
    }


@app.get("/api/agents/{agent_id}")
async def get_custom_agent(agent_id: str):
    """Get a specific custom agent."""
    agent = custom_agent_manager.get_agent(agent_id)
    if not agent:
        return JSONResponse({"error": "Agent not found"}, status_code=404)
    return agent.to_dict()


@app.put("/api/agents/{agent_id}")
async def update_custom_agent(agent_id: str, payload: AgentUpdate):
    """Update a custom agent."""
    agent = custom_agent_manager.get_agent(agent_id)
    if not agent:
        return JSONResponse({"error": "Agent not found"}, status_code=404)

    data = payload.model_dump(exclude_unset=True)

    if "name" in data:
        agent.name = data["name"]
    if "specialty" in data:
        agent.specialty = data["specialty"]
    if "guidance" in data:
        agent.guidance = data["guidance"]
    if "voice_id" in data:
        agent.voice_id = data["voice_id"]
    if "color" in data:
        agent.color = data["color"]
    if "avatar_emoji" in data:
        agent.avatar_emoji = data["avatar_emoji"]
    if "is_active" in data:
        agent.is_active = data["is_active"]

    filepath = custom_agent_manager.save_agent(agent)

    return {
        "status": "updated",
        "agent": agent.to_dict(),
        "filepath": filepath,
    }


@app.delete("/api/agents/{agent_id}")
async def delete_custom_agent(agent_id: str):
    """Delete a custom agent."""
    success = custom_agent_manager.delete_agent(agent_id)
    if not success:
        return JSONResponse({"error": "Agent not found or could not be deleted"}, status_code=404)
    return {"status": "deleted"}


@app.get("/api/agents/templates")
async def get_agent_templates():
    """Get available agent templates."""
    return list_templates()


# =============================================================================
# WEBSOCKET
# =============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for realtime session events."""
    await manager.connect(websocket)
    await manager.send(websocket, "connected", {"status": "connected"})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web.app:app", host="0.0.0.0", port=5001, reload=True)
