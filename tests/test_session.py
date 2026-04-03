from pathlib import Path

import lib.session as session_module


def test_parse_producer_scores_handles_aliases_and_fallbacks():
    response = """
    Rod: 7/10
    King scored 8 out of 10
    Lovecraft score: 11
    Borges: 0/10
    Writer 5: 6/10
    Tequila Bot: 9/10
    """
    agent_names = [
        "Rod Serling",
        "Stephen King",
        "H.P. Lovecraft",
        "Jorge Luis Borges",
        "Robert Stack",
        "RIP Tequila Bot",
    ]

    scores = session_module.parse_producer_scores(response, agent_names)

    assert scores == {
        "Rod Serling": 7,
        "Stephen King": 8,
        "H.P. Lovecraft": 10,
        "Jorge Luis Borges": 1,
        "Robert Stack": 6,
        "RIP Tequila Bot": 9,
    }


def test_session_orchestrator_emits_completion_and_saves_transcript(monkeypatch, tmp_path):
    class DummyAgent:
        def __init__(self, name, **kwargs):
            self.name = name

        def generate_response(self, context, story_context=None):
            return f"{self.name} writes a blood-soaked beat."

    monkeypatch.setattr(session_module, "Agent", DummyAgent)

    events = []
    orchestrator = session_module.SessionOrchestrator(
        lambda event, payload: events.append((event, payload))
    )
    config = {
        "mode": "horror",
        "rounds": 1,
        "temperature": 0.9,
        "producer_enabled": False,
        "voice_enabled": False,
        "include_custom_agents": False,
        "prompt": "Storm cellar mystery",
        "transcript_dir": str(tmp_path),
    }

    orchestrator.initialize("Storm cellar mystery", config)
    orchestrator.run_session(1)

    completed_event = next(
        payload
        for event, payload in events
        if event == session_module.SessionEvent.SESSION_COMPLETED
    )

    transcript_path = completed_event["transcript_path"]
    assert transcript_path is not None
    transcript_text = Path(transcript_path).read_text(encoding="utf-8")
    assert "Storm cellar mystery" in transcript_text
    assert "Rod Serling" in transcript_text
    assert completed_event["leaderboard"] == []
