from types import SimpleNamespace

from lib.agents import Agent


class DummyCompletions:
    def __init__(self, content: str):
        self.content = content
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=self.content),
                )
            ]
        )


class DummyClient:
    def __init__(self, content: str):
        self.chat = SimpleNamespace(completions=DummyCompletions(content))


def test_generate_response_preserves_prompt_and_truncates_recent_context():
    agent = Agent(
        name="Tester",
        model="fake/model",
        system_prompt="Base prompt",
        window_size=4,
    )
    dummy_client = DummyClient("Fresh contribution.")
    agent.client = dummy_client

    context = [
        {"role": "user", "content": "Original prompt stays intact."},
        {"role": "assistant", "content": "A" * 700, "name": "Agent 1"},
        {"role": "assistant", "content": "B" * 700, "name": "Agent 2"},
        {"role": "assistant", "content": "C" * 700, "name": "Agent 3"},
        {"role": "assistant", "content": "D" * 700, "name": "Agent 4"},
        {"role": "assistant", "content": "E" * 700, "name": "Agent 5"},
    ]

    response = agent.generate_response(context, story_context="CENTER TABLE")

    assert response == "Fresh contribution."
    messages = dummy_client.chat.completions.calls[0]["messages"]
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "Base prompt"
    assert messages[1]["content"] == "Original prompt stays intact."
    # story_context is injected as a separate user message at the end
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "CENTER TABLE"
    # system + original prompt + 4 windowed turns + story_context = 7
    assert len(messages) == 7
    assert all(
        msg["content"].startswith("...") and len(msg["content"]) == 503
        for msg in messages[2:-1]
    )


def test_generate_response_strips_ellipsis_echoes():
    agent = Agent(
        name="Tester",
        model="fake/model",
        system_prompt="Base prompt",
    )
    agent.client = DummyClient("... echoed setup. New sentence.")

    response = agent.generate_response(
        [{"role": "user", "content": "Prompt"}],
    )

    assert response == "New sentence."


def test_structured_output_extracts_json_key():
    """When response_format and json_key are set, extract the target field."""
    agent = Agent(
        name="Tester",
        model="fake/model",
        system_prompt="Base prompt",
        response_format={"type": "json_object"},
        json_key="line",
    )
    agent.client = DummyClient('{"line": "Cassian draws his rapier and steps forward."}')

    response = agent.generate_response(
        [{"role": "user", "content": "Prompt"}],
    )

    assert response == "Cassian draws his rapier and steps forward."


def test_structured_output_passes_response_format_to_api():
    """Verify response_format is forwarded in the API call kwargs."""
    agent = Agent(
        name="Tester",
        model="fake/model",
        system_prompt="Base prompt",
        response_format={"type": "json_object"},
        json_key="line",
    )
    dummy_client = DummyClient('{"line": "test"}')
    agent.client = dummy_client

    agent.generate_response([{"role": "user", "content": "Prompt"}])

    call_kwargs = dummy_client.chat.completions.calls[0]
    assert call_kwargs["response_format"] == {"type": "json_object"}


def test_structured_output_falls_back_on_bad_json():
    """When model returns non-JSON despite response_format, fall back to raw text."""
    agent = Agent(
        name="Tester",
        model="fake/model",
        system_prompt="Base prompt",
        response_format={"type": "json_object"},
        json_key="line",
    )
    agent.client = DummyClient("Cassian steps forward with rapier drawn.")

    response = agent.generate_response(
        [{"role": "user", "content": "Prompt"}],
    )

    # Falls back to raw text since JSON parsing fails
    assert response == "Cassian steps forward with rapier drawn."


def test_structured_output_falls_back_on_missing_key():
    """When JSON is valid but target key is missing, fall back to raw text."""
    agent = Agent(
        name="Tester",
        model="fake/model",
        system_prompt="Base prompt",
        response_format={"type": "json_object"},
        json_key="line",
    )
    agent.client = DummyClient('{"wrong_key": "some content"}')

    response = agent.generate_response(
        [{"role": "user", "content": "Prompt"}],
    )

    assert response == '{"wrong_key": "some content"}'


def test_no_response_format_omits_param_from_api_call():
    """When response_format is None, it should not appear in API kwargs."""
    agent = Agent(
        name="Tester",
        model="fake/model",
        system_prompt="Base prompt",
    )
    dummy_client = DummyClient("Plain text.")
    agent.client = dummy_client

    agent.generate_response([{"role": "user", "content": "Prompt"}])

    call_kwargs = dummy_client.chat.completions.calls[0]
    assert "response_format" not in call_kwargs


def test_parse_json_response_valid():
    data = Agent.parse_json_response('{"assessment": "Good round.", "scores": {"A": 7}}')
    assert data == {"assessment": "Good round.", "scores": {"A": 7}}


def test_parse_json_response_invalid():
    assert Agent.parse_json_response("not json at all") is None
    assert Agent.parse_json_response("") is None
