import os
import importlib
import importlib.util
import threading
import time
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from lib.custom_agents import CustomAgentManager


os.environ.setdefault("WRITERS_ROOM_SKIP_API_VALIDATION", "1")
os.environ.setdefault("OPENROUTER_API_KEY", "sk-or-v1-test-token")


def fresh_web_app_module(
    monkeypatch,
    *,
    completed_retention_seconds=60 * 60,
    stale_timeout_seconds=60 * 60 * 2,
):
    web_app_module = importlib.import_module("web.app")
    monkeypatch.setattr(
        web_app_module,
        "session_manager",
        web_app_module.SessionManager(
            completed_session_retention_seconds=completed_retention_seconds,
            stale_session_timeout_seconds=stale_timeout_seconds,
        ),
    )
    monkeypatch.setattr(
        web_app_module,
        "manager",
        web_app_module.ConnectionManager(event_buffer_size=16),
    )
    return web_app_module


def create_session(
    web_app_module,
    *,
    active=False,
    transcript=None,
    brief=None,
    final_draft=None,
    pipeline_dir=None,
):
    session = web_app_module.session_manager.create_session()
    web_app_module.session_manager.mark_active(session.session_id, active)
    web_app_module.session_manager.set_artifact_paths(
        session.session_id,
        transcript=transcript,
        brief=brief,
        final_draft=final_draft,
        pipeline_dir=pipeline_dir,
    )
    return session.session_id


def test_index_route_renders():
    web_app_module = importlib.import_module("web.app")

    with TestClient(web_app_module.app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "Launch Console" in response.text
    assert "/static/css/style.css" in response.text


def test_agents_page_renders():
    web_app_module = importlib.import_module("web.app")

    with TestClient(web_app_module.app) as client:
        response = client.get("/agents")

    assert response.status_code == 200
    assert "Custom Agents" in response.text
    assert "/static/css/style.css" in response.text


def test_agent_templates_route_is_not_shadowed():
    web_app_module = importlib.import_module("web.app")

    with TestClient(web_app_module.app) as client:
        response = client.get("/api/agents/templates")

    assert response.status_code == 200
    payload = response.json()
    assert "literary_master" in payload
    assert payload["literary_master"]["name"] == "Literary Master"


def test_agents_page_uses_defined_theme_tokens():
    web_app_module = importlib.import_module("web.app")

    with TestClient(web_app_module.app) as client:
        response = client.get("/agents")

    assert response.status_code == 200
    assert "--border-color" not in response.text
    assert "--accent-green" not in response.text
    assert "--accent-red" not in response.text
    assert "var(--border)" in response.text
    assert "var(--success)" in response.text
    assert "var(--error)" in response.text


def test_runtime_has_websocket_transport():
    assert importlib.util.find_spec("websockets") or importlib.util.find_spec("wsproto")


def test_custom_agent_api_supports_create_update_and_delete(monkeypatch, tmp_path):
    web_app_module = fresh_web_app_module(monkeypatch)
    manager = CustomAgentManager(tmp_path)
    monkeypatch.setattr(web_app_module, "custom_agent_manager", manager)

    with TestClient(web_app_module.app) as client:
        create_response = client.post(
            "/api/agents",
            json={
                "name": "Line Editor",
                "specialty": "Tight prose",
                "guidance": "Trim every sentence.",
                "voice_id": "echo",
                "color": "#654321",
                "avatar_emoji": "pencil2",
            },
        )
        assert create_response.status_code == 200
        created_agent = create_response.json()["agent"]

        list_response = client.get("/api/agents")
        assert list_response.status_code == 200
        assert [agent["name"] for agent in list_response.json()["agents"]] == ["Line Editor"]

        update_response = client.put(
            f"/api/agents/{created_agent['id']}",
            json={
                "name": "Lead Line Editor",
                "is_active": False,
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["agent"]["name"] == "Lead Line Editor"
        assert update_response.json()["agent"]["is_active"] is False

        fetch_response = client.get(f"/api/agents/{created_agent['id']}")
        assert fetch_response.status_code == 200
        assert fetch_response.json()["name"] == "Lead Line Editor"

        delete_response = client.delete(f"/api/agents/{created_agent['id']}")
        assert delete_response.status_code == 200
        assert manager.list_agents() == []


def test_custom_agent_api_rejects_duplicate_names(monkeypatch, tmp_path):
    web_app_module = fresh_web_app_module(monkeypatch)
    manager = CustomAgentManager(tmp_path)
    manager.save_agent(
        web_app_module.CustomAgent(
            id="",
            name="Line Editor",
            specialty="Tight prose",
            guidance="Trim every sentence.",
        )
    )
    monkeypatch.setattr(web_app_module, "custom_agent_manager", manager)

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/agents",
            json={
                "name": "Line Editor",
                "specialty": "Sharper dialogue",
                "guidance": "Cut anything soft.",
            },
        )

    assert response.status_code == 400
    assert "already exists" in response.json()["error"]


def test_status_reports_last_transcript(monkeypatch):
    web_app_module = fresh_web_app_module(monkeypatch)
    session_id = create_session(
        web_app_module,
        transcript="transcripts/web_session_20260402_120000.txt",
        brief="transcripts/web_session_20260402_120000_brief.html",
    )

    with TestClient(web_app_module.app) as client:
        response = client.get(f"/api/status?session_id={session_id}")

    assert response.status_code == 200
    assert response.json()["session_id"] == session_id
    assert response.json()["last_transcript"] == "transcripts/web_session_20260402_120000.txt"
    assert response.json()["last_brief"] == "transcripts/web_session_20260402_120000_brief.html"
    assert response.json()["mode_info"]["name"] == "Horror"


def test_latest_brief_route_returns_html(monkeypatch, tmp_path):
    web_app_module = fresh_web_app_module(monkeypatch)
    transcripts_dir = Path(web_app_module.TRANSCRIPTS_DIR)
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    brief_path = transcripts_dir / "test_latest_brief.html"
    brief_path.write_text("<html><body>Campaign Debrief</body></html>", encoding="utf-8")
    session_id = create_session(web_app_module, brief=str(brief_path))

    with TestClient(web_app_module.app) as client:
        response = client.get(f"/briefs/latest?session_id={session_id}")

    assert response.status_code == 200
    assert "Campaign Debrief" in response.text
    brief_path.unlink(missing_ok=True)


def test_latest_final_draft_route_returns_markdown(monkeypatch):
    web_app_module = fresh_web_app_module(monkeypatch)
    final_dir = Path(web_app_module.FINAL_DIR)
    final_dir.mkdir(parents=True, exist_ok=True)
    draft_path = final_dir / "test_latest_final.md"
    draft_path.write_text("# Final Draft\n\nIt hummed all night.", encoding="utf-8")
    session_id = create_session(web_app_module, final_draft=str(draft_path))

    with TestClient(web_app_module.app) as client:
        response = client.get(f"/drafts/latest?session_id={session_id}")

    assert response.status_code == 200
    assert "Final Draft" in response.text
    assert "It hummed all night." in response.text
    draft_path.unlink(missing_ok=True)


def test_latest_final_draft_route_rejects_paths_outside_transcripts(monkeypatch, tmp_path):
    web_app_module = fresh_web_app_module(monkeypatch)
    draft_path = tmp_path / "rogue_final.md"
    draft_path.write_text("# Not allowed", encoding="utf-8")
    session_id = create_session(web_app_module, final_draft=str(draft_path))

    with TestClient(web_app_module.app) as client:
        response = client.get(f"/drafts/latest?session_id={session_id}")

    assert response.status_code == 403


def test_latest_final_draft_route_returns_404_when_missing(monkeypatch):
    web_app_module = fresh_web_app_module(monkeypatch)
    session_id = create_session(web_app_module)

    with TestClient(web_app_module.app) as client:
        response = client.get(f"/drafts/latest?session_id={session_id}")

    assert response.status_code == 404


def test_latest_brief_route_rejects_paths_outside_transcripts(monkeypatch, tmp_path):
    web_app_module = fresh_web_app_module(monkeypatch)
    brief_path = tmp_path / "latest_brief.html"
    brief_path.write_text("<html><body>Campaign Debrief</body></html>", encoding="utf-8")
    session_id = create_session(web_app_module, brief=str(brief_path))

    with TestClient(web_app_module.app) as client:
        response = client.get(f"/briefs/latest?session_id={session_id}")

    assert response.status_code == 403


def test_status_reports_last_final_draft(monkeypatch):
    web_app_module = fresh_web_app_module(monkeypatch)
    session_id = create_session(
        web_app_module,
        transcript="transcripts/web_session_20260409_120000.txt",
        brief="transcripts/web_session_20260409_120000_brief.html",
        final_draft="final/260409_midnight-bell_final.md",
    )

    with TestClient(web_app_module.app) as client:
        response = client.get(f"/api/status?session_id={session_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["last_final_draft"] == "final/260409_midnight-bell_final.md"


def test_start_api_accepts_produce_final_draft_toggle(monkeypatch):
    web_app_module = fresh_web_app_module(monkeypatch)
    captured = {"calls": []}

    class DummyThread:
        def __init__(self, target, args, daemon, name):
            captured["calls"].append(
                {"target": target, "args": args, "daemon": daemon, "name": name}
            )

        def start(self):
            captured["started"] = True

        def join(self, timeout=None):
            return None

        def is_alive(self):
            return False

    monkeypatch.setattr(web_app_module.threading, "Thread", DummyThread)

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/start",
            json={
                "prompt": "A lighthouse keeper hears her own voice on the radio.",
                "notes": "Quiet dread, no monsters.",
                "rounds": 2,
                "temperature": 0.9,
                "producer_enabled": True,
                "fire_worst": False,
                "mode": "horror",
                "voice_enabled": False,
                "include_custom_agents": False,
                "produce_final_draft": True,
            },
        )

    assert response.status_code == 200
    assert response.json()["session_id"]
    worker_call = next(
        call for call in captured["calls"] if call["target"] is web_app_module.run_session_thread
    )
    _, _, _, config = worker_call["args"]
    assert config["produce_final_draft"] is True
    assert config["mode"] == "horror"


def test_start_api_forces_dnd_to_drop_final_draft(monkeypatch):
    web_app_module = fresh_web_app_module(monkeypatch)
    captured = {"calls": []}

    class DummyThread:
        def __init__(self, target, args, daemon, name):
            captured["calls"].append(
                {"target": target, "args": args, "daemon": daemon, "name": name}
            )

        def start(self):
            captured["started"] = True

        def join(self, timeout=None):
            return None

        def is_alive(self):
            return False

    monkeypatch.setattr(web_app_module.threading, "Thread", DummyThread)

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/start",
            json={
                "prompt": "Recover the ember crown.",
                "rounds": 1,
                "mode": "dnd",
                "produce_final_draft": True,
            },
        )

    assert response.status_code == 200
    worker_call = next(
        call for call in captured["calls"] if call["target"] is web_app_module.run_session_thread
    )
    _, _, _, config = worker_call["args"]
    assert config["produce_final_draft"] is False


def test_start_api_forces_dnd_web_sessions_into_app_safe_config(monkeypatch):
    web_app_module = fresh_web_app_module(monkeypatch)
    captured = {"calls": []}

    class DummyThread:
        def __init__(self, target, args, daemon, name):
            captured["calls"].append(
                {"target": target, "args": args, "daemon": daemon, "name": name}
            )

        def start(self):
            captured["started"] = True

        def join(self, timeout=None):
            return None

        def is_alive(self):
            return False

    monkeypatch.setattr(web_app_module.threading, "Thread", DummyThread)

    with TestClient(web_app_module.app) as client:
        response = client.post(
            "/api/start",
            json={
                "prompt": "Spooky roller disco",
                "notes": "Keep it playable and neon-gothic.",
                "rounds": 2,
                "temperature": 0.8,
                "producer_enabled": True,
                "fire_worst": True,
                "mode": "dnd",
                "voice_enabled": False,
                "include_custom_agents": True,
            },
        )

    assert response.status_code == 200
    assert captured["started"] is True

    worker_call = next(
        call for call in captured["calls"] if call["target"] is web_app_module.run_session_thread
    )
    _, _, _, config = worker_call["args"]
    assert config["notes"] == "Keep it playable and neon-gothic."
    assert config["producer_enabled"] is False
    assert config["include_custom_agents"] is False


def test_websocket_event_ids_are_monotonic(monkeypatch):
    web_app_module = fresh_web_app_module(monkeypatch)
    session_id = create_session(web_app_module, active=True)

    with TestClient(web_app_module.app) as client:
        with client.websocket_connect(f"/ws?session_id={session_id}") as websocket:
            connected = websocket.receive_json()
            assert connected["data"]["session_id"] == session_id

            for round_num in range(1, 4):
                web_app_module.emit_event(
                    session_id,
                    "round_started",
                    {"round": round_num, "total": 3},
                )

            messages = [websocket.receive_json() for _ in range(3)]

    assert [message["event_id"] for message in messages] == [1, 2, 3]
    assert [message["data"]["round"] for message in messages] == [1, 2, 3]


def test_websocket_replays_missed_events(monkeypatch):
    web_app_module = fresh_web_app_module(monkeypatch)
    session_id = create_session(web_app_module, active=True)

    with TestClient(web_app_module.app) as client:
        with client.websocket_connect(f"/ws?session_id={session_id}") as websocket:
            websocket.receive_json()
            web_app_module.emit_event(
                session_id,
                "agent_response",
                {"agent": "Rod Serling", "response": "Beat one.", "round": 1},
            )
            first_message = websocket.receive_json()

        web_app_module.emit_event(
            session_id,
            "agent_response",
            {"agent": "Stephen King", "response": "Beat two.", "round": 1},
        )

        with client.websocket_connect(
            f"/ws?session_id={session_id}&last_event_id={first_message['event_id']}"
        ) as websocket:
            connected = websocket.receive_json()
            replayed_message = websocket.receive_json()

    assert connected["data"]["replayed_count"] == 1
    assert replayed_message["event_id"] == first_message["event_id"] + 1
    assert replayed_message["data"]["response"] == "Beat two."


def test_websocket_keeps_sessions_isolated(monkeypatch):
    web_app_module = fresh_web_app_module(monkeypatch)
    first_session_id = create_session(web_app_module, active=True)
    second_session_id = create_session(web_app_module, active=True)

    with TestClient(web_app_module.app) as client:
        with client.websocket_connect(f"/ws?session_id={first_session_id}") as first_socket:
            with client.websocket_connect(f"/ws?session_id={second_session_id}") as second_socket:
                first_socket.receive_json()
                second_socket.receive_json()

                web_app_module.emit_event(
                    first_session_id,
                    "round_started",
                    {"round": 1, "total": 2},
                )
                web_app_module.emit_event(
                    second_session_id,
                    "round_started",
                    {"round": 9, "total": 9},
                )

                first_message = first_socket.receive_json()
                second_message = second_socket.receive_json()

    assert first_message["session_id"] == first_session_id
    assert first_message["data"]["round"] == 1
    assert second_message["session_id"] == second_session_id
    assert second_message["data"]["round"] == 9


def test_session_manager_cleans_up_finished_thread_after_exit(monkeypatch):
    web_app_module = fresh_web_app_module(
        monkeypatch,
        completed_retention_seconds=0.01,
    )
    session = web_app_module.session_manager.create_session()

    thread = threading.Thread(target=lambda: None)
    thread.start()
    web_app_module.session_manager.attach_thread(session.session_id, thread)
    thread.join(timeout=1)

    snapshot = None
    for _ in range(20):
        snapshot = web_app_module.session_manager.get_session_snapshot(session.session_id)
        if snapshot and snapshot["thread"] is None and snapshot["active"] is False:
            break
        time.sleep(0.01)

    assert snapshot is not None
    assert snapshot["thread"] is None
    assert snapshot["active"] is False

    time.sleep(0.02)
    removed_session_ids = web_app_module.session_manager.cleanup_stale_sessions()
    assert session.session_id in removed_session_ids
