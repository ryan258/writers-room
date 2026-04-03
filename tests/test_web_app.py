import importlib

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from lib.custom_agents import CustomAgentManager


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

    with TestClient(web_app_module.app) as client:
        response = client.get("/api/status")

    assert response.status_code == 200
    assert response.json()["last_transcript"] == "transcripts/web_session_20260402_120000.txt"
