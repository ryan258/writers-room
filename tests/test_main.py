from urllib import error as urllib_error

import main as main_module
from lib import custom_agents as custom_agents_module
from lib.personalities import DEFAULT_MODEL, get_agent_roster
from lib.story_state import StoryStateManager
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
    manager = StoryStateManager("A cursed bell tolls under the abbey.", mode="dnd")

    main_module.display_story_state(manager)

    output = capsys.readouterr().out
    assert "Open Threads" in output
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


def test_save_transcript_uses_round_grouping_for_dnd(tmp_path):
    filename = tmp_path / "dnd_transcript.txt"
    manager = StoryStateManager("The manor has begun to breathe.", mode="dnd")
    manager.process_contribution(
        "The hall falls silent as the portrait eyes turn toward you.",
        "Dungeon Master",
        1,
    )

    saved_path = main_module.save_transcript(
        "The manor has begun to breathe.",
        [
            {"role": "user", "content": "ignored for dnd transcript"},
            {
                "role": "assistant",
                "name": "Dungeon Master",
                "content": "The hall falls silent as the portrait eyes turn toward you.",
                "round": 1,
            },
            {
                "role": "assistant",
                "name": "Rod Serling",
                "content": "Cassian lifts his lantern and asks who in this house still has a pulse.",
                "round": 1,
            },
        ],
        story_state=manager.state,
        filename=str(filename),
    )

    text = filename.read_text(encoding="utf-8")

    assert saved_path == str(filename)
    assert "WRITERS ROOM D&D TABLE TRANSCRIPT" in text
    assert "ADVENTURE HOOK: The manor has begun to breathe." in text
    assert "ROUND 1" in text
    assert "[USER]" not in text


def test_main_create_agent_mode_imports_lib_custom_agents(monkeypatch):
    called = {}

    class Args:
        create_agent = True

    def fake_interactive_create_agent():
        called["interactive"] = True

    monkeypatch.setattr(main_module, "parse_args", lambda: Args())
    monkeypatch.setattr(custom_agents_module, "interactive_create_agent", fake_interactive_create_agent)

    main_module.main()

    assert called["interactive"] is True
