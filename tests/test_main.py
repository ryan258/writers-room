import argparse
from urllib import error as urllib_error

import pytest

import main as main_module
from lib import custom_agents as custom_agents_module
from lib.personalities import DEFAULT_MODEL, get_agent_roster
from lib.session_turns import (
    build_clean_dnd_history,
    clean_dnd_table_talk,
    looks_like_dnd_meta_response,
)


class DummyResponse:
    def __init__(self, payload: bytes):
        self.payload = payload

    def read(self) -> bytes:
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_validate_api_key_uses_key_endpoint(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-token")

    def fake_urlopen(request, timeout=0):
        assert request.full_url == "https://openrouter.ai/api/v1/key"
        assert request.get_method() == "GET"
        assert request.headers["Authorization"] == "Bearer sk-or-v1-test-token"
        return DummyResponse(b'{"data": {"label": "demo", "limit_remaining": 10}}')

    monkeypatch.setattr(main_module.urllib_request, "urlopen", fake_urlopen)

    is_valid, message = main_module.validate_api_key()

    assert is_valid is True
    assert message == "API key validated successfully"


def test_validate_api_key_reports_invalid_token(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-token")

    def fake_urlopen(request, timeout=0):
        raise urllib_error.HTTPError(
            request.full_url,
            401,
            "Unauthorized",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr(main_module.urllib_request, "urlopen", fake_urlopen)

    is_valid, message = main_module.validate_api_key()

    assert is_valid is False
    assert message == "API key is invalid or expired"


def test_default_model_keeps_current_nemotron_free_alias():
    assert DEFAULT_MODEL == "nvidia/nemotron-3-super-120b-a12b:free"


def test_dnd_roster_prompts_do_not_append_generic_mode_context():
    roster = get_agent_roster("dnd")

    assert roster[0]["name"] == "Dungeon Master"
    assert "STORY MODE:" not in roster[0]["system_prompt"]
    assert "ATMOSPHERE:" not in roster[0]["system_prompt"]


def test_display_story_state_hides_story_needs_for_dnd(capsys):
    main_module.display_story_state(
        {
            "mode": "dnd",
            "current_act": 1,
            "tension_level": 4,
            "word_count": 12,
            "story_needs": ["Ignore me"],
        }
    )

    output = capsys.readouterr().out
    assert "Words: 12" in output
    assert "Open Threads" not in output
    assert "Story needs" not in output


def test_clean_dnd_table_talk_extracts_quoted_scene_from_meta_response():
    response = (
        'We need to produce DM turn. Let\'s craft: "The chandelier sways above the feast hall '
        'while a heartbeat thumps beneath the floorboards. A masked servant points toward the locked pantry door. '
        'What do you do?"'
    )

    cleaned = clean_dnd_table_talk(response)

    assert cleaned.startswith("The chandelier sways above the feast hall")
    assert "We need to" not in cleaned


def test_meta_detection_catches_obvious_prompt_leakage():
    leaked = "Okay, I am the DM. I must frame the scene, present the pressure, and invite the party to act."

    assert looks_like_dnd_meta_response(leaked) is True


def test_meta_detection_catches_any_round_number_preamble():
    leaked = "Round 5: I need to frame the next beat, raise the tension, and ask what they do."

    assert looks_like_dnd_meta_response(leaked) is True


def test_build_clean_dnd_history_filters_meta_turns():
    history = [
        {"role": "user", "content": "Run a D&D session inspired by a haunted manor."},
        {"role": "assistant", "name": "Dungeon Master", "content": "Okay, I am the DM. I must frame the scene."},
        {
            "role": "assistant",
            "name": "Dungeon Master",
            "content": "The study door trembles on its hinges while a heartbeat knocks through the walls. What do you do?",
        },
    ]

    cleaned = build_clean_dnd_history(history)

    assert len(cleaned) == 2
    assert cleaned[0]["role"] == "user"
    assert cleaned[1]["content"].startswith("The study door trembles on its hinges")


class DummySessionOrchestrator:
    def __init__(self, event_callback):
        self.event_callback = event_callback
        self.initialize_calls = []
        self.run_calls = []
        self.resume_calls = []
        self.config = {}
        DummySessionOrchestrator.instance = self

    def initialize(self, prompt, config):
        self.initialize_calls.append((prompt, config))
        self.config = config
        self.event_callback(
            main_module.SessionEvent.SESSION_STARTED,
            {
                "prompt": prompt,
                "rounds": config["rounds"],
                "config": config,
                "mode": config["mode"],
                "agent_roster": [
                    {
                        "name": "Rod Serling",
                        "color": "#00FFFF",
                        "specialty": "dread",
                    }
                ],
            },
        )

    def run_session(self, rounds):
        self.run_calls.append(rounds)
        self._emit_round(round_num=1, total=rounds)
        self._emit_completion()

    def resume(self, additional_rounds):
        self.resume_calls.append(additional_rounds)
        self.event_callback(
            main_module.SessionEvent.SESSION_RESUMED,
            {
                "additional_rounds": additional_rounds,
                "starting_round": len(self.run_calls) + sum(self.resume_calls[:-1]) + 1,
                "config": self.config,
                "agent_roster": [
                    {
                        "name": "Rod Serling",
                        "color": "#00FFFF",
                        "specialty": "dread",
                    }
                ],
            },
        )
        self._emit_round(round_num=2, total=1 + additional_rounds)
        self._emit_completion()

    def _emit_round(self, *, round_num, total):
        mode = self.config["mode"]
        self.event_callback(
            main_module.SessionEvent.STORY_STATE_UPDATE,
            {
                "round": round_num,
                "state": {
                    "mode": mode,
                    "current_act": 1,
                    "tension_level": 4,
                    "word_count": 42,
                    "story_needs": [] if mode == "dnd" else ["Establish a central conflict or mystery"],
                },
            },
        )
        self.event_callback(
            main_module.SessionEvent.ROUND_STARTED,
            {"round": round_num, "total": total},
        )
        self.event_callback(
            main_module.SessionEvent.AGENT_RESPONSE,
            {
                "agent": "Rod Serling",
                "response": "A door sighed open.",
                "color": "#00FFFF",
                "round": round_num,
            },
        )
        if self.config.get("producer_enabled"):
            self.event_callback(
                main_module.SessionEvent.PRODUCER_VERDICT,
                {
                    "response": "Solid round.\n\nRod Serling: 8/10",
                    "scores": {"Rod Serling": 8},
                    "leaderboard": [
                        {
                            "name": "Rod Serling",
                            "average": 8.0,
                            "scores": [8],
                        }
                    ],
                    "round": round_num,
                },
            )

    def _emit_completion(self):
        leaderboard = []
        winner = None
        if self.config.get("producer_enabled"):
            leaderboard = [
                {
                    "name": "Rod Serling",
                    "average": 8.0,
                    "scores": [8],
                }
            ]
            winner = leaderboard[0]

        self.event_callback(
            main_module.SessionEvent.SESSION_COMPLETED,
            {
                "leaderboard": leaderboard,
                "winner": winner,
                "worst": None,
                "story_state": None,
                "transcript_path": "transcripts/demo_transcript.txt",
                "brief_path": "transcripts/demo_brief.html",
                "final_draft_path": None,
                "pipeline_dir": None,
            },
        )


def test_main_horror_mode_uses_orchestrator_sink(monkeypatch, capsys):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-token")
    monkeypatch.setattr(main_module, "SessionOrchestrator", DummySessionOrchestrator)
    monkeypatch.setattr(
        main_module,
        "parse_args",
        lambda: argparse.Namespace(
            create_agent=False,
            run_pipeline=None,
            retry_pipeline=None,
            skip_validation=True,
            model="demo-model",
            mode="horror",
            rounds=1,
            no_continue=True,
            temperature=None,
            no_producer=False,
            fire_worst=False,
        ),
    )
    prompts = iter(["A storm cellar opens beneath the farmhouse."])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(prompts))

    main_module.main()

    output = capsys.readouterr().out
    orchestrator = DummySessionOrchestrator.instance
    assert orchestrator.run_calls == [1]
    assert orchestrator.initialize_calls[0][0] == "A storm cellar opens beneath the farmhouse."
    assert orchestrator.config["include_custom_agents"] is False
    assert orchestrator.config["producer_enabled"] is True
    assert "Rod Serling (dread)" in output
    assert "THE PRODUCER'S VERDICT" in output
    assert "FINAL LEADERBOARD" in output
    assert "WINNER: Rod Serling" in output
    assert "Transcript saved to: transcripts/demo_transcript.txt" in output


def test_main_resume_uses_orchestrator_resume(monkeypatch, capsys):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-token")
    monkeypatch.setattr(main_module, "SessionOrchestrator", DummySessionOrchestrator)
    monkeypatch.setattr(
        main_module,
        "parse_args",
        lambda: argparse.Namespace(
            create_agent=False,
            run_pipeline=None,
            retry_pipeline=None,
            skip_validation=True,
            model="demo-model",
            mode="horror",
            rounds=1,
            no_continue=False,
            temperature=None,
            no_producer=False,
            fire_worst=False,
        ),
    )
    prompts = iter(
        [
            "The ferry returns with no passengers.",
            "2",
            "n",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(prompts))

    main_module.main()

    output = capsys.readouterr().out
    orchestrator = DummySessionOrchestrator.instance
    assert orchestrator.run_calls == [1]
    assert orchestrator.resume_calls == [2]
    assert "Continuing with 2 more round(s)" in output
    assert "ROUNDS COMPLETE (Total: 3)" in output


def test_main_dnd_mode_disables_producer_and_story_needs(monkeypatch, capsys):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-token")
    monkeypatch.setattr(main_module, "SessionOrchestrator", DummySessionOrchestrator)
    monkeypatch.setattr(
        main_module,
        "parse_args",
        lambda: argparse.Namespace(
            create_agent=False,
            run_pipeline=None,
            retry_pipeline=None,
            skip_validation=True,
            model="demo-model",
            mode="dnd",
            rounds=1,
            no_continue=True,
            temperature=None,
            no_producer=False,
            fire_worst=False,
        ),
    )
    prompts = iter(["Recover the ember crown from the drowned keep."])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(prompts))

    main_module.main()

    output = capsys.readouterr().out
    orchestrator = DummySessionOrchestrator.instance
    assert orchestrator.config["producer_enabled"] is False
    assert orchestrator.config["include_custom_agents"] is False
    assert "D&D mode runs without The Producer" in output
    assert "THE PRODUCER'S VERDICT" not in output
    assert "Story needs" not in output


def test_main_create_agent_mode_imports_lib_custom_agents(monkeypatch):
    called = {}

    def fake_interactive_create_agent():
        called["interactive"] = True

    monkeypatch.setattr(
        main_module,
        "parse_args",
        lambda: argparse.Namespace(create_agent=True),
    )
    monkeypatch.setattr(custom_agents_module, "interactive_create_agent", fake_interactive_create_agent)

    main_module.main()

    assert called["interactive"] is True


def test_main_run_pipeline_mode_uses_saved_final_draft(monkeypatch):
    called = {}

    def fake_generate_pipeline_report_from_draft(**kwargs):
        called["kwargs"] = kwargs
        return "pipelines/the-closet"

    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-token")
    monkeypatch.setattr(
        main_module,
        "parse_args",
        lambda: argparse.Namespace(
            create_agent=False,
            run_pipeline="final/260409_the-closet_final.md",
            retry_pipeline=None,
            skip_validation=True,
            model="demo-model",
        ),
    )
    monkeypatch.setattr(
        main_module,
        "generate_pipeline_report_from_draft",
        fake_generate_pipeline_report_from_draft,
    )
    monkeypatch.setattr(main_module, "get_pipeline_failures", lambda pipeline_dir: None)

    main_module.main()

    assert called["kwargs"]["draft_path"] == "final/260409_the-closet_final.md"
    assert called["kwargs"]["model"] == "demo-model"


def test_main_retry_pipeline_mode_delegates_to_retry_helper(monkeypatch):
    called = {}

    def fake_retry_failed_pipeline_items(**kwargs):
        called["kwargs"] = kwargs
        return "pipelines/the-closet"

    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-token")
    monkeypatch.setattr(
        main_module,
        "parse_args",
        lambda: argparse.Namespace(
            create_agent=False,
            run_pipeline=None,
            retry_pipeline="final/260409_the-closet_final.md",
            skip_validation=True,
            model="demo-model",
        ),
    )
    monkeypatch.setattr(
        main_module,
        "retry_failed_pipeline_items",
        fake_retry_failed_pipeline_items,
    )
    monkeypatch.setattr(main_module, "get_pipeline_failures", lambda pipeline_dir: None)

    main_module.main()

    assert called["kwargs"]["draft_path"] == "final/260409_the-closet_final.md"
    assert called["kwargs"]["model"] == "demo-model"


def test_main_run_pipeline_mode_exits_nonzero_when_pipeline_has_failures(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-token")
    monkeypatch.setattr(
        main_module,
        "parse_args",
        lambda: argparse.Namespace(
            create_agent=False,
            run_pipeline="final/260409_the-closet_final.md",
            retry_pipeline=None,
            skip_validation=True,
            model="demo-model",
        ),
    )
    monkeypatch.setattr(
        main_module,
        "generate_pipeline_report_from_draft",
        lambda **kwargs: "pipelines/260409_the-closet",
    )
    monkeypatch.setattr(
        main_module,
        "get_pipeline_failures",
        lambda pipeline_dir: {
            "status_failed": False,
            "marketing_failed": ["landing-page"],
        },
    )

    with pytest.raises(SystemExit) as excinfo:
        main_module.main()

    assert excinfo.value.code == 1


def test_main_retry_pipeline_mode_exits_nonzero_when_pipeline_has_failures(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-token")
    monkeypatch.setattr(
        main_module,
        "parse_args",
        lambda: argparse.Namespace(
            create_agent=False,
            run_pipeline=None,
            retry_pipeline="final/260409_the-closet_final.md",
            skip_validation=True,
            model="demo-model",
        ),
    )
    monkeypatch.setattr(
        main_module,
        "retry_failed_pipeline_items",
        lambda **kwargs: "pipelines/260409_the-closet",
    )
    monkeypatch.setattr(
        main_module,
        "get_pipeline_failures",
        lambda pipeline_dir: {
            "status_failed": True,
            "marketing_failed": [],
        },
    )

    with pytest.raises(SystemExit) as excinfo:
        main_module.main()

    assert excinfo.value.code == 1
