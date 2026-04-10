#!/usr/bin/env python3
"""
Writers Room Web Interface
FastAPI backend for real-time collaborative storytelling.
"""

import asyncio
import inspect
import os
import sys
import threading
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add repo root to path for lib imports
ROOT_DIR = Path(__file__).resolve().parents[1]
TRANSCRIPTS_DIR = ROOT_DIR / "transcripts"
FINAL_DIR = ROOT_DIR / "final"
PIPELINES_DIR = ROOT_DIR / "pipelines"
sys.path.append(str(ROOT_DIR))

load_dotenv()

from lib.config import ConfigError, RuntimeConfig, build_runtime_config, should_skip_api_validation
from lib.custom_agents import CustomAgentManager, CustomAgent, list_templates
from lib.personalities import STORY_MODES, DEFAULT_MODEL
from lib.session import SessionOrchestrator, SessionEvent
from lib.voice import get_voice_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.loop = asyncio.get_running_loop()
    try:
        app.state.runtime_config, app.state.runtime_config_message = build_runtime_config(
            validate_api_key=not should_skip_api_validation(),
        )
    except ConfigError as exc:
        raise RuntimeError(f"Web startup configuration failed: {exc}") from exc
    yield


app = FastAPI(lifespan=lifespan)

# Static files and templates
WEB_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))
TEMPLATE_RESPONSE_REQUEST_FIRST = (
    tuple(inspect.signature(Jinja2Templates.TemplateResponse).parameters)[1] == "request"
)

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

DEFAULT_EVENT_BUFFER_SIZE = 200
DEFAULT_COMPLETED_SESSION_RETENTION_SECONDS = 60 * 60
DEFAULT_STALE_SESSION_TIMEOUT_SECONDS = 60 * 60 * 2
DEFAULT_THREAD_JOIN_TIMEOUT_SECONDS = 0.25


@dataclass
class SessionRecord:
    session_id: str
    orchestrator: Optional[SessionOrchestrator] = None
    thread: Optional[threading.Thread] = None
    active: bool = False
    last_transcript: Optional[str] = None
    last_brief: Optional[str] = None
    last_final_draft: Optional[str] = None
    last_pipeline_dir: Optional[str] = None
    created_at: float = field(default_factory=time.monotonic)
    updated_at: float = field(default_factory=time.monotonic)

    def touch(self) -> None:
        self.updated_at = time.monotonic()


@dataclass(frozen=True)
class BufferedEvent:
    session_id: str
    event_id: int
    event: str
    data: Dict[str, Any]

    def as_message(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "event_id": self.event_id,
            "event": self.event,
            "data": self.data,
        }


class SessionManager:
    def __init__(
        self,
        *,
        completed_session_retention_seconds: float = DEFAULT_COMPLETED_SESSION_RETENTION_SECONDS,
        stale_session_timeout_seconds: float = DEFAULT_STALE_SESSION_TIMEOUT_SECONDS,
        thread_join_timeout_seconds: float = DEFAULT_THREAD_JOIN_TIMEOUT_SECONDS,
    ) -> None:
        self._lock = threading.RLock()
        self._sessions: Dict[str, SessionRecord] = {}
        self._latest_session_id: Optional[str] = None
        self._completed_session_retention_seconds = completed_session_retention_seconds
        self._stale_session_timeout_seconds = stale_session_timeout_seconds
        self._thread_join_timeout_seconds = thread_join_timeout_seconds

    def create_session(self) -> SessionRecord:
        session_id = uuid.uuid4().hex
        record = SessionRecord(session_id=session_id, active=True)
        with self._lock:
            self._sessions[session_id] = record
            self._latest_session_id = session_id
        return record

    def _resolve_session_id_locked(self, session_id: Optional[str]) -> Optional[str]:
        if session_id is not None:
            return session_id if session_id in self._sessions else None
        if self._latest_session_id and self._latest_session_id in self._sessions:
            return self._latest_session_id
        return None

    def resolve_session_id(self, session_id: Optional[str] = None) -> Optional[str]:
        with self._lock:
            return self._resolve_session_id_locked(session_id)

    def get_session_snapshot(self, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        with self._lock:
            resolved_id = self._resolve_session_id_locked(session_id)
            if resolved_id is None:
                return None
            record = self._sessions[resolved_id]
            return {
                "session_id": record.session_id,
                "orchestrator": record.orchestrator,
                "thread": record.thread,
                "active": record.active,
                "last_transcript": record.last_transcript,
                "last_brief": record.last_brief,
                "last_final_draft": record.last_final_draft,
                "last_pipeline_dir": record.last_pipeline_dir,
                "created_at": record.created_at,
                "updated_at": record.updated_at,
            }

    def get_orchestrator(self, session_id: Optional[str]) -> Optional[SessionOrchestrator]:
        with self._lock:
            resolved_id = self._resolve_session_id_locked(session_id)
            if resolved_id is None:
                return None
            return self._sessions[resolved_id].orchestrator

    def set_orchestrator(self, session_id: str, orchestrator: SessionOrchestrator) -> None:
        with self._lock:
            record = self._sessions.get(session_id)
            if record is None:
                return
            record.orchestrator = orchestrator
            record.active = True
            record.touch()

    def attach_thread(self, session_id: str, thread: threading.Thread) -> None:
        with self._lock:
            record = self._sessions.get(session_id)
            if record is None:
                return
            record.thread = thread
            record.active = True
            record.touch()
        watcher = threading.Thread(
            target=self._watch_thread,
            args=(session_id, thread),
            daemon=True,
            name=f"writers-room-join-{session_id[:8]}",
        )
        watcher.start()

    def _watch_thread(self, session_id: str, thread: threading.Thread) -> None:
        thread.join()
        with self._lock:
            record = self._sessions.get(session_id)
            if record is None or record.thread is not thread:
                return
            record.thread = None
            record.active = False
            record.touch()

    def clear_session_artifacts(self, session_id: str) -> None:
        with self._lock:
            record = self._sessions.get(session_id)
            if record is None:
                return
            record.last_transcript = None
            record.last_brief = None
            record.last_final_draft = None
            record.last_pipeline_dir = None
            record.touch()

    def mark_active(self, session_id: str, active: bool) -> None:
        with self._lock:
            record = self._sessions.get(session_id)
            if record is None:
                return
            record.active = active
            record.touch()

    def touch(self, session_id: str) -> None:
        with self._lock:
            record = self._sessions.get(session_id)
            if record is not None:
                record.touch()

    def update_artifacts(self, session_id: str, orchestrator: Optional[SessionOrchestrator]) -> None:
        if orchestrator is None:
            return
        with self._lock:
            record = self._sessions.get(session_id)
            if record is None:
                return
            record.orchestrator = orchestrator
            record.last_transcript = orchestrator.transcript_path
            record.last_brief = getattr(orchestrator, "brief_path", None)
            record.last_final_draft = getattr(orchestrator, "final_draft_path", None)
            record.last_pipeline_dir = getattr(orchestrator, "pipeline_dir", None)
            record.touch()

    def set_artifact_paths(
        self,
        session_id: str,
        *,
        transcript: Optional[str] = None,
        brief: Optional[str] = None,
        final_draft: Optional[str] = None,
        pipeline_dir: Optional[str] = None,
    ) -> None:
        with self._lock:
            record = self._sessions.get(session_id)
            if record is None:
                return
            record.last_transcript = transcript
            record.last_brief = brief
            record.last_final_draft = final_draft
            record.last_pipeline_dir = pipeline_dir
            record.touch()

    def cleanup_stale_sessions(self) -> List[str]:
        now = time.monotonic()
        timed_out: List[tuple[str, SessionRecord]] = []
        removable: List[str] = []

        with self._lock:
            items = list(self._sessions.items())

        for session_id, record in items:
            thread = record.thread
            thread_alive = thread.is_alive() if thread else False
            age = now - record.updated_at
            if record.active and thread_alive and age > self._stale_session_timeout_seconds:
                timed_out.append((session_id, record))
            elif (not record.active) and age > self._completed_session_retention_seconds:
                removable.append(session_id)

        for session_id, record in timed_out:
            orchestrator = record.orchestrator
            if orchestrator is not None:
                orchestrator.stop()
            thread = record.thread
            if thread and thread.is_alive() and threading.current_thread() is not thread:
                thread.join(timeout=self._thread_join_timeout_seconds)
            with self._lock:
                current = self._sessions.get(session_id)
                if current is None or current is not record:
                    continue
                current.active = current.thread.is_alive() if current.thread else False
                if not current.active:
                    current.thread = None
                current.touch()

        removed: List[str] = []
        with self._lock:
            for session_id in removable:
                record = self._sessions.get(session_id)
                if record is None or record.active:
                    continue
                if now - record.updated_at <= self._completed_session_retention_seconds:
                    continue
                del self._sessions[session_id]
                removed.append(session_id)

            if self._latest_session_id not in self._sessions:
                self._latest_session_id = next(reversed(self._sessions), None) if self._sessions else None

        return removed

# Custom agent manager
custom_agent_manager = CustomAgentManager()


class ConnectionManager:
    def __init__(self, *, event_buffer_size: int = DEFAULT_EVENT_BUFFER_SIZE) -> None:
        self._lock = threading.RLock()
        self._event_buffer_size = event_buffer_size
        self.active_connections: Dict[str, List[WebSocket]] = defaultdict(list)
        self._event_buffers: Dict[str, deque[BufferedEvent]] = {}
        self._event_counters: Dict[str, int] = defaultdict(int)

    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
        *,
        last_event_id: Optional[int] = None,
    ) -> None:
        await websocket.accept()
        replay_events: List[BufferedEvent] = []
        latest_event_id = 0
        with self._lock:
            self.active_connections[session_id].append(websocket)
            replay_events = [
                event
                for event in self._event_buffers.get(session_id, deque())
                if last_event_id is None or event.event_id > last_event_id
            ]
            latest_event_id = self._event_counters.get(session_id, 0)
        await self.send(
            websocket,
            "connected",
            {
                "status": "connected",
                "session_id": session_id,
                "last_event_id": latest_event_id,
                "replayed_count": len(replay_events),
            },
            session_id=session_id,
        )
        for replay_event in replay_events:
            await websocket.send_json(replay_event.as_message())

    def disconnect(self, websocket: WebSocket, session_id: Optional[str] = None) -> None:
        with self._lock:
            if session_id is not None:
                session_connections = self.active_connections.get(session_id, [])
                if websocket in session_connections:
                    session_connections.remove(websocket)
                if not session_connections and session_id in self.active_connections:
                    del self.active_connections[session_id]
                return
            for active_session_id, session_connections in list(self.active_connections.items()):
                if websocket in session_connections:
                    session_connections.remove(websocket)
                if not session_connections:
                    del self.active_connections[active_session_id]

    async def send(
        self,
        websocket: WebSocket,
        event: str,
        data: Dict[str, Any],
        *,
        session_id: Optional[str] = None,
        event_id: Optional[int] = None,
    ) -> None:
        message = {"event": event, "data": data}
        if session_id is not None:
            message["session_id"] = session_id
        if event_id is not None:
            message["event_id"] = event_id
        await websocket.send_json(message)

    async def broadcast(self, session_id: str, event: str, data: Dict[str, Any]) -> Optional[int]:
        with self._lock:
            next_event_id = self._event_counters[session_id] + 1
            self._event_counters[session_id] = next_event_id
            buffer = self._event_buffers.setdefault(
                session_id,
                deque(maxlen=self._event_buffer_size),
            )
            buffered_event = BufferedEvent(
                session_id=session_id,
                event_id=next_event_id,
                event=event,
                data=data,
            )
            buffer.append(buffered_event)
            connections = list(self.active_connections.get(session_id, []))

        if not connections:
            return next_event_id

        stale: List[WebSocket] = []
        for ws in connections:
            try:
                await ws.send_json(buffered_event.as_message())
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(ws, session_id=session_id)
        return next_event_id

    def drop_session(self, session_id: str) -> None:
        with self._lock:
            self.active_connections.pop(session_id, None)
            self._event_buffers.pop(session_id, None)
            self._event_counters.pop(session_id, None)


session_manager = SessionManager()
manager = ConnectionManager()


def _is_allowed_brief_path(candidate: Path) -> bool:
    """Only serve generated HTML briefs from the transcripts directory."""
    try:
        resolved = candidate.resolve()
        transcripts_root = TRANSCRIPTS_DIR.resolve()
    except OSError:
        return False

    if resolved.suffix.lower() != ".html":
        return False

    try:
        resolved.relative_to(transcripts_root)
    except ValueError:
        return False

    return True


def _is_allowed_final_draft_path(candidate: Path) -> bool:
    """Only serve final-draft Markdown files from approved artifact directories."""
    try:
        resolved = candidate.resolve()
        allowed_roots = [TRANSCRIPTS_DIR.resolve(), FINAL_DIR.resolve()]
    except OSError:
        return False

    if resolved.suffix.lower() != ".md":
        return False

    for root in allowed_roots:
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue

    return False


def _is_allowed_transcript_path(candidate: Path) -> bool:
    """Only serve transcript text files from the transcripts directory."""
    try:
        resolved = candidate.resolve()
        transcripts_root = TRANSCRIPTS_DIR.resolve()
    except OSError:
        return False

    if resolved.suffix.lower() != ".txt":
        return False

    try:
        resolved.relative_to(transcripts_root)
    except ValueError:
        return False

    return True


def _resolve_pipeline_index(pipeline_dir: str | Path) -> Path | None:
    """Return the ``index.md`` path for a pipeline directory, if it's allowed."""
    try:
        resolved_dir = Path(pipeline_dir).resolve()
        pipelines_root = PIPELINES_DIR.resolve()
    except OSError:
        return None

    try:
        resolved_dir.relative_to(pipelines_root)
    except ValueError:
        return None

    index_path = resolved_dir / "index.md"
    if not index_path.exists():
        return None
    return index_path


def cleanup_stale_state() -> None:
    """Prune expired sessions and their buffered websocket state."""
    for session_id in session_manager.cleanup_stale_sessions():
        manager.drop_session(session_id)


def get_requested_session_id(request: Request) -> Optional[str]:
    """Resolve the requested session id from query string or header."""
    return request.query_params.get("session_id") or request.headers.get("X-Session-ID")


def get_session_snapshot_for_request(request: Request) -> Optional[Dict[str, Any]]:
    cleanup_stale_state()
    return session_manager.get_session_snapshot(get_requested_session_id(request))


def emit_event(session_id: str, event: str, data: Dict[str, Any]) -> None:
    """Thread-safe event emitter for SessionOrchestrator."""
    session_manager.touch(session_id)
    loop = getattr(app.state, "loop", None)
    if loop:
        asyncio.run_coroutine_threadsafe(manager.broadcast(session_id, event, data), loop)


def render_template(request: Request, template_name: str, context: Optional[Dict[str, Any]] = None):
    """Support both legacy and current Starlette TemplateResponse signatures."""
    template_context = {"request": request}
    if context:
        template_context.update(context)

    if TEMPLATE_RESPONSE_REQUEST_FIRST:
        return templates.TemplateResponse(request, template_name, template_context)

    return templates.TemplateResponse(template_name, template_context)


def get_runtime_config() -> RuntimeConfig:
    runtime_config = getattr(app.state, "runtime_config", None)
    if runtime_config is None:
        raise RuntimeError("Runtime config has not been initialized")
    return runtime_config


def run_session_thread(session_id: str, prompt: str, rounds: int, config: Dict[str, Any]) -> None:
    orchestrator: Optional[SessionOrchestrator] = None
    try:
        session_manager.mark_active(session_id, True)
        session_manager.clear_session_artifacts(session_id)
        orchestrator = SessionOrchestrator(
            lambda event, payload: emit_event(session_id, event, payload),
            runtime_config=get_runtime_config(),
        )
        session_manager.set_orchestrator(session_id, orchestrator)
        orchestrator.initialize(prompt, config)
        orchestrator.run_session(rounds)
    except Exception as exc:
        emit_event(session_id, SessionEvent.ERROR, {"message": str(exc)})
    finally:
        session_manager.update_artifacts(session_id, orchestrator)
        session_manager.mark_active(session_id, False)


class StartRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    notes: Optional[str] = None
    rounds: int = Field(3, ge=1, le=10)
    temperature: float = Field(0.9, ge=0, le=2)
    producer_enabled: bool = True
    fire_worst: bool = False
    mode: str = "horror"
    voice_enabled: bool = False
    include_custom_agents: bool = True
    produce_final_draft: bool = False
    model: Optional[str] = None


class ContinueRequest(BaseModel):
    session_id: Optional[str] = None
    rounds: int = Field(3, ge=1, le=10)


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
    return render_template(
        request,
        "index.html",
        {
            "modes": STORY_MODES,
            "mode_order": ["dnd", "fantasy", "horror", "literary", "noir", "sci-fi", "comedy"],
            "default_mode": "dnd",
        },
    )


@app.get("/agents")
async def agents_page(request: Request):
    """Render the custom agents UI."""
    return render_template(request, "agents.html")


@app.post("/api/start")
async def start_session(req: StartRequest):
    """Start a new writers room session."""
    cleanup_stale_state()

    prompt = req.prompt.strip()
    if not prompt:
        return JSONResponse({"error": "Prompt is required"}, status_code=400)

    config = req.model_dump()
    config["model"] = req.model or DEFAULT_MODEL
    config["prompt"] = prompt
    config["notes"] = (req.notes or "").strip()
    if req.mode == "dnd":
        config["producer_enabled"] = False
        config["include_custom_agents"] = False
        config["produce_final_draft"] = False

    session = session_manager.create_session()

    # Start session in background thread
    thread = threading.Thread(
        target=run_session_thread,
        args=(session.session_id, prompt, req.rounds, config),
        daemon=True,
        name=f"writers-room-{session.session_id[:8]}",
    )
    thread.start()
    session_manager.attach_thread(session.session_id, thread)

    return {"status": "started", "session_id": session.session_id}


def continue_session_thread(session_id: str, additional_rounds: int) -> None:
    orchestrator = session_manager.get_orchestrator(session_id)
    if orchestrator is None:
        return
    try:
        session_manager.mark_active(session_id, True)
        session_manager.clear_session_artifacts(session_id)
        orchestrator.resume(additional_rounds)
    except Exception as exc:
        emit_event(session_id, SessionEvent.ERROR, {"message": str(exc)})
    finally:
        session_manager.update_artifacts(session_id, orchestrator)
        session_manager.mark_active(session_id, False)


@app.post("/api/continue")
async def continue_session(req: ContinueRequest):
    """Continue a completed session for additional rounds."""
    cleanup_stale_state()

    session_id = session_manager.resolve_session_id(req.session_id)
    if not session_id:
        return JSONResponse({"error": "No session to continue. Start one first."}, status_code=400)

    snapshot = session_manager.get_session_snapshot(session_id)
    if snapshot and snapshot.get("active"):
        return JSONResponse({"error": "Session already active"}, status_code=400)

    orchestrator = session_manager.get_orchestrator(session_id)
    if not orchestrator:
        return JSONResponse({"error": "No session to continue. Start one first."}, status_code=400)

    thread = threading.Thread(
        target=continue_session_thread,
        args=(session_id, req.rounds),
        daemon=True,
        name=f"writers-room-resume-{session_id[:8]}",
    )
    thread.start()
    session_manager.attach_thread(session_id, thread)

    return {"status": "resumed", "additional_rounds": req.rounds, "session_id": session_id}


@app.get("/api/status")
async def get_status(request: Request):
    """Get current session status."""
    snapshot = get_session_snapshot_for_request(request)
    story_state = None
    config = {}
    agent_roster = []

    orch = snapshot.get("orchestrator") if snapshot else None
    if orch:
        if orch.story_manager:
            story_state = orch._build_story_state_payload()
        config = orch.config
        agent_roster = [
            {
                "name": agent.get("name"),
                "color": agent.get("color"),
                "specialty": agent.get("specialty", ""),
            }
            for agent in getattr(orch, "agents", [])
        ]

    return {
        "session_id": snapshot.get("session_id") if snapshot else None,
        "active": snapshot.get("active", False) if snapshot else False,
        "config": config,
        "mode_info": STORY_MODES.get(config.get("mode", "horror"), {}),
        "story_state": story_state,
        "agent_roster": agent_roster,
        "last_transcript": snapshot.get("last_transcript") if snapshot else None,
        "last_brief": snapshot.get("last_brief") if snapshot else None,
        "last_final_draft": snapshot.get("last_final_draft") if snapshot else None,
        "last_pipeline_dir": snapshot.get("last_pipeline_dir") if snapshot else None,
    }


@app.get("/briefs/latest", response_class=FileResponse)
async def get_latest_brief(request: Request):
    """Return the most recent generated session brief."""
    snapshot = get_session_snapshot_for_request(request)
    brief_path = snapshot.get("last_brief") if snapshot else None
    if not brief_path:
        return JSONResponse({"error": "No session brief has been generated yet."}, status_code=404)

    html_path = Path(brief_path)
    if not _is_allowed_brief_path(html_path):
        return JSONResponse({"error": "Invalid brief path."}, status_code=403)

    if not html_path.exists():
        return JSONResponse({"error": "The latest session brief could not be found on disk."}, status_code=404)

    return FileResponse(str(html_path), media_type="text/html")


@app.get("/drafts/latest", response_class=FileResponse)
async def get_latest_final_draft(request: Request):
    """Return the most recent generated final-draft Markdown file."""
    snapshot = get_session_snapshot_for_request(request)
    draft_path = snapshot.get("last_final_draft") if snapshot else None
    if not draft_path:
        return JSONResponse({"error": "No final draft has been generated yet."}, status_code=404)

    md_path = Path(draft_path)
    if not _is_allowed_final_draft_path(md_path):
        return JSONResponse({"error": "Invalid final draft path."}, status_code=403)

    if not md_path.exists():
        return JSONResponse({"error": "The latest final draft could not be found on disk."}, status_code=404)

    return FileResponse(str(md_path), media_type="text/markdown")


@app.get("/transcripts/latest", response_class=FileResponse)
async def get_latest_transcript(request: Request):
    """Return the most recent saved transcript file."""
    snapshot = get_session_snapshot_for_request(request)
    transcript_path = snapshot.get("last_transcript") if snapshot else None
    if not transcript_path:
        return JSONResponse({"error": "No transcript has been saved yet."}, status_code=404)

    txt_path = Path(transcript_path)
    if not _is_allowed_transcript_path(txt_path):
        return JSONResponse({"error": "Invalid transcript path."}, status_code=403)

    if not txt_path.exists():
        return JSONResponse({"error": "The latest transcript could not be found on disk."}, status_code=404)

    return FileResponse(str(txt_path), media_type="text/plain")


@app.get("/pipelines/latest", response_class=FileResponse)
async def get_latest_pipeline_index(request: Request):
    """Return the ``index.md`` of the most recent pipeline directory."""
    snapshot = get_session_snapshot_for_request(request)
    pipeline_dir = snapshot.get("last_pipeline_dir") if snapshot else None
    if not pipeline_dir:
        return JSONResponse({"error": "No pipeline has been generated yet."}, status_code=404)

    index_path = _resolve_pipeline_index(pipeline_dir)
    if index_path is None:
        return JSONResponse(
            {"error": "Pipeline index is missing or outside the allowed directory."},
            status_code=404,
        )

    return FileResponse(str(index_path), media_type="text/markdown")


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
    try:
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
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    return {
        "status": "created",
        "agent": agent.to_dict(),
        "filepath": filepath,
    }


@app.get("/api/agents/templates")
async def get_agent_templates():
    """Get available agent templates."""
    return list_templates()


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

    updated_data = agent.to_dict()
    updated_data.update(payload.model_dump(exclude_unset=True))

    try:
        updated_agent = CustomAgent.from_dict(updated_data)
        filepath = custom_agent_manager.save_agent(updated_agent)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)

    return {
        "status": "updated",
        "agent": updated_agent.to_dict(),
        "filepath": filepath,
    }


@app.delete("/api/agents/{agent_id}")
async def delete_custom_agent(agent_id: str):
    """Delete a custom agent."""
    success = custom_agent_manager.delete_agent(agent_id)
    if not success:
        return JSONResponse({"error": "Agent not found or could not be deleted"}, status_code=404)
    return {"status": "deleted"}


# =============================================================================
# WEBSOCKET
# =============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for realtime session events."""
    cleanup_stale_state()
    requested_session_id = websocket.query_params.get("session_id")
    resolved_session_id = session_manager.resolve_session_id(requested_session_id)
    if resolved_session_id is None:
        await websocket.accept()
        await manager.send(
            websocket,
            "connected",
            {
                "status": "idle",
                "session_id": None,
                "last_event_id": 0,
                "replayed_count": 0,
            },
        )
        await websocket.close()
        return

    last_event_id_raw = websocket.query_params.get("last_event_id")
    try:
        last_event_id = int(last_event_id_raw) if last_event_id_raw is not None else None
    except ValueError:
        last_event_id = None

    await manager.connect(
        websocket,
        resolved_session_id,
        last_event_id=last_event_id,
    )
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id=resolved_session_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web.app:app", host="0.0.0.0", port=5001, reload=True)
