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
    monkeypatch.setattr(
        session_module,
        "render_session_brief",
        lambda **kwargs: str(tmp_path / "web_session_20260404_120000_brief.html"),
    )

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


def test_session_orchestrator_builds_dnd_roster(monkeypatch):
    class DummyAgent:
        def __init__(self, name, **kwargs):
            self.name = name
            self.system_prompt = kwargs["system_prompt"]

        def generate_response(self, context, story_context=None):
            return f"{self.name} takes a turn."

    monkeypatch.setattr(session_module, "Agent", DummyAgent)

    events = []
    orchestrator = session_module.SessionOrchestrator(
        lambda event, payload: events.append((event, payload))
    )
    config = {
        "mode": "dnd",
        "rounds": 1,
        "temperature": 0.8,
        "producer_enabled": False,
        "voice_enabled": False,
        "include_custom_agents": True,
        "prompt": "Recover the ember crown from the drowned keep.",
    }

    orchestrator.initialize("Recover the ember crown from the drowned keep.", config)

    assert orchestrator.config["include_custom_agents"] is False
    assert orchestrator.config["producer_enabled"] is False
    assert orchestrator.conversation_history[0]["content"].startswith(
        "Run an original Dungeons & Dragons 2024 (5.5) session"
    )

    roster_names = [agent["name"] for agent in orchestrator.agents]
    assert roster_names[0] == "Dungeon Master"
    assert "Rod Serling" in roster_names
    assert any(agent["specialty"].startswith("Level 9") for agent in orchestrator.agents[1:])
    assert orchestrator.producer is None

    started_event = next(
        payload
        for event, payload in events
        if event == session_module.SessionEvent.SESSION_STARTED
    )
    assert started_event["mode"] == "dnd"
    assert started_event["agent_roster"][0]["name"] == "Dungeon Master"


def test_session_orchestrator_cleans_dnd_prompt_leakage(monkeypatch, tmp_path):
    class DummyAgent:
        def __init__(self, name, **kwargs):
            self.name = name

        def generate_response(self, context, story_context=None):
            if self.name == "Dungeon Master":
                return (
                    'We need to produce DM turn. Let\'s craft: "The mirror ball jerks once, '
                    'spraying green light across a ring of skates that keep moving without feet. '
                    'The DJ booth counts backward from thirteen. What do you do?"'
                )
            return (
                'Speak only as a player. "I move on the booth now, using the rink rails as cover '
                'before that countdown finishes."'
            )

    monkeypatch.setattr(session_module, "Agent", DummyAgent)
    monkeypatch.setattr(
        session_module,
        "render_session_brief",
        lambda **kwargs: str(tmp_path / "dnd_brief.html"),
    )

    events = []
    orchestrator = session_module.SessionOrchestrator(
        lambda event, payload: events.append((event, payload))
    )
    config = {
        "mode": "dnd",
        "rounds": 1,
        "temperature": 0.8,
        "producer_enabled": True,
        "voice_enabled": False,
        "include_custom_agents": True,
        "prompt": "Survive the haunted roller disco.",
    }

    orchestrator.initialize("Survive the haunted roller disco.", config)
    orchestrator.run_session(1)

    responses = [
        payload["response"]
        for event, payload in events
        if event == session_module.SessionEvent.AGENT_RESPONSE
    ]

    assert responses
    assert all("we need to" not in response.lower() for response in responses)
    assert all("speak only as" not in response.lower() for response in responses)
    assert responses[0].startswith("The mirror ball jerks once")


def test_session_resume_continues_from_correct_round(monkeypatch, tmp_path):
    """Resuming a completed session picks up at the next round number."""
    class DummyAgent:
        def __init__(self, name, **kwargs):
            self.name = name

        def generate_response(self, context, story_context=None):
            return f"{self.name} contributes."

    monkeypatch.setattr(session_module, "Agent", DummyAgent)
    monkeypatch.setattr(
        session_module,
        "render_session_brief",
        lambda **kwargs: str(tmp_path / "brief.html"),
    )

    events = []
    orchestrator = session_module.SessionOrchestrator(
        lambda event, payload: events.append((event, payload))
    )
    config = {
        "mode": "horror",
        "rounds": 2,
        "temperature": 0.9,
        "producer_enabled": False,
        "voice_enabled": False,
        "include_custom_agents": False,
        "prompt": "A door that shouldn't be open.",
        "transcript_dir": str(tmp_path),
    }

    orchestrator.initialize("A door that shouldn't be open.", config)
    orchestrator.run_session(2)

    # Session completed with 2 rounds
    assert orchestrator._completed_rounds() == 2
    assert not orchestrator.active

    # Count contributions so far
    initial_contributions = len([
        m for m in orchestrator.conversation_history if m.get("role") == "assistant"
    ])

    # Resume for 1 more round
    events.clear()
    orchestrator.resume(1)

    # Verify resumed event fired with correct round
    resumed = next(
        payload for event, payload in events
        if event == session_module.SessionEvent.SESSION_RESUMED
    )
    assert resumed["starting_round"] == 3
    assert resumed["additional_rounds"] == 1

    # Verify round 3 actually ran
    round_events = [
        payload for event, payload in events
        if event == session_module.SessionEvent.ROUND_STARTED
    ]
    assert round_events[0]["round"] == 3

    # Verify new contributions were appended
    final_contributions = len([
        m for m in orchestrator.conversation_history if m.get("role") == "assistant"
    ])
    assert final_contributions > initial_contributions

    # Verify session completed again
    completed = any(
        event == session_module.SessionEvent.SESSION_COMPLETED
        for event, _ in events
    )
    assert completed
    assert not orchestrator.active


def test_parse_producer_json_extracts_scores():
    """Structured JSON producer response yields clean scores."""
    import json

    raw = json.dumps({
        "assessment": "Strong round with good teamwork.",
        "scores": {
            "Rod Serling": 8,
            "Stephen King": 7,
            "H.P. Lovecraft": 6,
        },
    })
    agent_names = ["Rod Serling", "Stephen King", "H.P. Lovecraft"]

    scores = session_module.SessionOrchestrator._parse_producer_json(raw, agent_names)

    assert scores == {"Rod Serling": 8, "Stephen King": 7, "H.P. Lovecraft": 6}


def test_parse_producer_json_clamps_values():
    """Scores outside 1-10 are clamped."""
    import json

    raw = json.dumps({"scores": {"A": 0, "B": 15}})
    scores = session_module.SessionOrchestrator._parse_producer_json(raw, ["A", "B"])

    assert scores == {"A": 1, "B": 10}


def test_parse_producer_json_returns_none_on_bad_json():
    """Non-JSON or missing scores key returns None for regex fallback."""
    assert session_module.SessionOrchestrator._parse_producer_json(
        "not json", ["A"]
    ) is None
    assert session_module.SessionOrchestrator._parse_producer_json(
        '{"assessment": "ok"}', ["A"]
    ) is None
