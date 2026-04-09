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


def test_final_draft_off_by_default(monkeypatch, tmp_path):
    """Sessions without produce_final_draft don't run the editor."""
    class DummyAgent:
        def __init__(self, name, **kwargs):
            self.name = name

        def generate_response(self, context, story_context=None):
            return f"{self.name} writes a line."

    monkeypatch.setattr(session_module, "Agent", DummyAgent)
    monkeypatch.setattr(
        session_module,
        "render_session_brief",
        lambda **kwargs: str(tmp_path / "brief.html"),
    )
    called = {"count": 0}
    pipeline_called = {"count": 0}

    def fake_generate(**kwargs):
        called["count"] += 1
        return "ignored"

    def fake_pipeline(**kwargs):
        pipeline_called["count"] += 1
        return str(tmp_path / "pipelines" / "ignored")

    monkeypatch.setattr(session_module, "generate_final_draft", fake_generate)
    monkeypatch.setattr(session_module, "generate_pipeline_report_from_draft", fake_pipeline)

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
        "prompt": "A locked closet hums at night.",
        "transcript_dir": str(tmp_path),
    }

    orchestrator.initialize("A locked closet hums at night.", config)
    orchestrator.run_session(1)

    assert called["count"] == 0
    assert pipeline_called["count"] == 0
    assert orchestrator.final_draft_path is None
    assert orchestrator.final_draft_markdown is None
    assert orchestrator.pipeline_dir is None

    editor_events = [e for e, _ in events if e.startswith("editor_")]
    assert editor_events == []

    completed = next(
        payload for event, payload in events
        if event == session_module.SessionEvent.SESSION_COMPLETED
    )
    assert completed["final_draft_path"] is None
    assert completed["pipeline_dir"] is None


def test_final_draft_produces_markdown_and_file(monkeypatch, tmp_path):
    """With the toggle on, the editor runs and the file is saved."""
    class DummyAgent:
        def __init__(self, name, **kwargs):
            self.name = name

        def generate_response(self, context, story_context=None):
            return f"{self.name} contributes a beat."

    monkeypatch.setattr(session_module, "Agent", DummyAgent)
    monkeypatch.setattr(
        session_module,
        "render_session_brief",
        lambda **kwargs: str(tmp_path / "brief.html"),
    )

    expected_markdown = "# The Closet\n\nIt hummed all night, and no one slept."

    def fake_generate(**kwargs):
        emit = kwargs["emit"]
        emit("editor_thinking", {"stage": "structural"})
        emit("editor_response", {"stage": "structural", "preview": "draft", "length": 42})
        emit("editor_thinking", {"stage": "line"})
        emit("editor_response", {"stage": "line", "preview": "polished", "length": 50})
        return expected_markdown

    def fake_pipeline(**kwargs):
        output_dir = Path(kwargs["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "index.md").write_text("# Pipeline\n\nReady.", encoding="utf-8")
        return str(output_dir)

    monkeypatch.setattr(session_module, "generate_final_draft", fake_generate)
    monkeypatch.setattr(session_module, "generate_pipeline_report_from_draft", fake_pipeline)

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
        "prompt": "A locked closet hums at night.",
        "transcript_dir": str(tmp_path),
        "final_dir": str(tmp_path / "final"),
        "pipeline_dir": str(tmp_path / "pipelines"),
        "produce_final_draft": True,
    }

    orchestrator.initialize("A locked closet hums at night.", config)
    orchestrator.run_session(1)

    assert orchestrator.final_draft_markdown == expected_markdown
    assert orchestrator.final_draft_path is not None
    draft_path = Path(orchestrator.final_draft_path)
    assert draft_path.exists()
    assert draft_path.suffix == ".md"
    assert draft_path.stem.endswith("_final")
    assert draft_path.parent == tmp_path / "final"
    assert draft_path.read_text(encoding="utf-8") == expected_markdown
    assert orchestrator.pipeline_dir is not None
    pipeline_dir = Path(orchestrator.pipeline_dir)
    assert pipeline_dir.is_dir()
    assert pipeline_dir.parent == tmp_path / "pipelines"
    assert (pipeline_dir / "index.md").exists()

    editor_events = [e for e, _ in events if e.startswith("editor_")]
    assert editor_events == [
        "editor_thinking",
        "editor_response",
        "editor_thinking",
        "editor_response",
    ]

    completed = next(
        payload for event, payload in events
        if event == session_module.SessionEvent.SESSION_COMPLETED
    )
    assert completed["final_draft_path"] == str(draft_path)
    assert completed["pipeline_dir"] == str(pipeline_dir)


def test_final_draft_disabled_for_dnd(monkeypatch, tmp_path):
    """D&D mode never runs the editor, even with the toggle on."""
    class DummyAgent:
        def __init__(self, name, **kwargs):
            self.name = name

        def generate_response(self, context, story_context=None):
            return f"{self.name} takes a turn."

    monkeypatch.setattr(session_module, "Agent", DummyAgent)
    monkeypatch.setattr(
        session_module,
        "render_session_brief",
        lambda **kwargs: str(tmp_path / "brief.html"),
    )
    called = {"count": 0}
    pipeline_called = {"count": 0}

    def fake_generate(**kwargs):
        called["count"] += 1
        return "should not run"

    def fake_pipeline(**kwargs):
        pipeline_called["count"] += 1
        return str(tmp_path / "pipelines" / "ignored")

    monkeypatch.setattr(session_module, "generate_final_draft", fake_generate)
    monkeypatch.setattr(session_module, "generate_pipeline_report_from_draft", fake_pipeline)

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
        "include_custom_agents": False,
        "prompt": "Recover the ember crown.",
        "transcript_dir": str(tmp_path),
        "produce_final_draft": True,
    }

    orchestrator.initialize("Recover the ember crown.", config)
    assert orchestrator.config["produce_final_draft"] is False

    orchestrator.run_session(1)

    assert called["count"] == 0
    assert pipeline_called["count"] == 0
    assert orchestrator.final_draft_path is None
    assert orchestrator.pipeline_dir is None
    editor_events = [e for e, _ in events if e.startswith("editor_")]
    assert editor_events == []


def test_final_draft_failure_graceful(monkeypatch, tmp_path):
    """If the editor raises, the session still completes and the brief saves."""
    class DummyAgent:
        def __init__(self, name, **kwargs):
            self.name = name

        def generate_response(self, context, story_context=None):
            return f"{self.name} writes a line."

    monkeypatch.setattr(session_module, "Agent", DummyAgent)
    monkeypatch.setattr(
        session_module,
        "render_session_brief",
        lambda **kwargs: str(tmp_path / "brief.html"),
    )
    pipeline_called = {"count": 0}

    def broken_generate(**kwargs):
        raise RuntimeError("editor exploded")

    def fake_pipeline(**kwargs):
        pipeline_called["count"] += 1
        return str(tmp_path / "pipelines" / "ignored")

    monkeypatch.setattr(session_module, "generate_final_draft", broken_generate)
    monkeypatch.setattr(session_module, "generate_pipeline_report_from_draft", fake_pipeline)

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
        "prompt": "A storm rolls in at dusk.",
        "transcript_dir": str(tmp_path),
        "produce_final_draft": True,
    }

    orchestrator.initialize("A storm rolls in at dusk.", config)
    orchestrator.run_session(1)

    assert orchestrator.final_draft_markdown is None
    assert orchestrator.final_draft_path is None
    assert orchestrator.pipeline_dir is None
    assert pipeline_called["count"] == 0

    error_messages = [
        payload["message"]
        for event, payload in events
        if event == session_module.SessionEvent.ERROR
    ]
    assert any("Final draft failed" in msg for msg in error_messages)

    completed_events = [
        payload for event, payload in events
        if event == session_module.SessionEvent.SESSION_COMPLETED
    ]
    assert len(completed_events) == 1
    assert completed_events[0]["final_draft_path"] is None
    assert completed_events[0]["pipeline_dir"] is None
    assert completed_events[0]["transcript_path"] is not None


def test_brief_render_failure_emits_error_and_session_still_completes(monkeypatch, tmp_path):
    class DummyAgent:
        def __init__(self, name, **kwargs):
            self.name = name

        def generate_response(self, context, story_context=None):
            return f"{self.name} writes a line."

    monkeypatch.setattr(session_module, "Agent", DummyAgent)
    monkeypatch.setattr(
        session_module,
        "render_session_brief",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("brief exploded")),
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
        "prompt": "The floor remembers footsteps.",
        "transcript_dir": str(tmp_path),
    }

    orchestrator.initialize("The floor remembers footsteps.", config)
    orchestrator.run_session(1)

    error_messages = [
        payload["message"]
        for event, payload in events
        if event == session_module.SessionEvent.ERROR
    ]
    assert any("Brief render failed" in msg for msg in error_messages)

    completed = next(
        payload for event, payload in events
        if event == session_module.SessionEvent.SESSION_COMPLETED
    )
    assert completed["brief_path"] is None
    assert completed["transcript_path"] is not None


def test_session_orchestrator_producer_prompt_matches_structured_output(monkeypatch):
    class DummyAgent:
        def __init__(self, name, **kwargs):
            self.name = name
            self.system_prompt = kwargs["system_prompt"]
            self.response_format = kwargs.get("response_format")

        def generate_response(self, context, story_context=None):
            return f"{self.name} contributes."

    monkeypatch.setattr(session_module, "Agent", DummyAgent)

    orchestrator = session_module.SessionOrchestrator(lambda *_: None)
    orchestrator.initialize(
        "A ship arrives empty.",
        {
            "mode": "horror",
            "rounds": 1,
            "temperature": 0.9,
            "producer_enabled": True,
            "voice_enabled": False,
            "include_custom_agents": False,
            "prompt": "A ship arrives empty.",
        },
    )

    assert orchestrator.producer is not None
    assert orchestrator.producer.response_format == {"type": "json_object"}
    assert "respond with a JSON object only" in orchestrator.producer.system_prompt
    assert '"assessment"' in orchestrator.producer.system_prompt
    assert '"scores"' in orchestrator.producer.system_prompt
