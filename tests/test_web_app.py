import importlib
import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from lib.custom_agents import CustomAgentManager


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
    web_app_module = importlib.import_module("web.app")
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


def test_status_reports_last_transcript(monkeypatch):
    web_app_module = importlib.import_module("web.app")
    monkeypatch.setitem(web_app_module.current_session, "active", False)
    monkeypatch.setitem(
        web_app_module.current_session,
        "last_transcript",
        "transcripts/web_session_20260402_120000.txt",
    )
    monkeypatch.setitem(web_app_module.current_session, "orchestrator", None)
    monkeypatch.setitem(
        web_app_module.current_session,
        "last_brief",
        "transcripts/web_session_20260402_120000_brief.html",
    )

    with TestClient(web_app_module.app) as client:
        response = client.get("/api/status")

    assert response.status_code == 200
    assert response.json()["last_transcript"] == "transcripts/web_session_20260402_120000.txt"
    assert response.json()["last_brief"] == "transcripts/web_session_20260402_120000_brief.html"
    assert response.json()["mode_info"]["name"] == "Horror"


def test_latest_brief_route_returns_html(monkeypatch, tmp_path):
    web_app_module = importlib.import_module("web.app")
    transcripts_dir = Path(web_app_module.TRANSCRIPTS_DIR)
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    brief_path = transcripts_dir / "test_latest_brief.html"
    brief_path.write_text("<html><body>Campaign Debrief</body></html>", encoding="utf-8")
    monkeypatch.setitem(web_app_module.current_session, "last_brief", str(brief_path))

    with TestClient(web_app_module.app) as client:
        response = client.get("/briefs/latest")

    assert response.status_code == 200
    assert "Campaign Debrief" in response.text
    brief_path.unlink(missing_ok=True)


def test_latest_brief_route_rejects_paths_outside_transcripts(monkeypatch, tmp_path):
    web_app_module = importlib.import_module("web.app")
    brief_path = tmp_path / "latest_brief.html"
    brief_path.write_text("<html><body>Campaign Debrief</body></html>", encoding="utf-8")
    monkeypatch.setitem(web_app_module.current_session, "last_brief", str(brief_path))

    with TestClient(web_app_module.app) as client:
        response = client.get("/briefs/latest")

    assert response.status_code == 403


def test_start_api_forces_dnd_web_sessions_into_app_safe_config(monkeypatch):
    web_app_module = importlib.import_module("web.app")
    captured = {}

    class DummyThread:
        def __init__(self, target, args, daemon):
            captured["target"] = target
            captured["args"] = args
            captured["daemon"] = daemon

        def start(self):
            captured["started"] = True

    monkeypatch.setattr(web_app_module.threading, "Thread", DummyThread)
    monkeypatch.setitem(web_app_module.current_session, "active", False)

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

    _, _, config = captured["args"]
    assert config["notes"] == "Keep it playable and neon-gothic."
    assert config["producer_enabled"] is False
    assert config["include_custom_agents"] is False
