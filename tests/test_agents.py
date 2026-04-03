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
    assert "CENTER TABLE" in messages[0]["content"]
    assert messages[1]["content"] == "Original prompt stays intact."
    assert len(messages) == 6
    assert all(
        msg["content"].startswith("...") and len(msg["content"]) == 503
        for msg in messages[2:]
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
