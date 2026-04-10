from pathlib import Path

import pytest

import lib.custom_agents as custom_agents_module
from lib.custom_agents import CustomAgent, CustomAgentManager


def test_custom_agent_manager_crud_cycle(tmp_path):
    manager = CustomAgentManager(tmp_path)
    agent = CustomAgent(
        id="",
        name="Archivist",
        specialty="Continuity and callbacks",
        guidance="Keep the story coherent.",
        voice_id="nova",
        color="#123456",
        avatar_emoji="books",
    )

    saved_path = manager.save_agent(agent)
    assert tmp_path.joinpath(f"{agent.id}.json").exists()
    assert saved_path.endswith(f"{agent.id}.json")

    loaded = manager.get_agent(agent.id)
    assert loaded is not None
    assert loaded.name == "Archivist"

    loaded.name = "Lead Archivist"
    loaded.is_active = False
    manager.save_agent(loaded)

    all_agents = manager.list_agents()
    assert [item.name for item in all_agents] == ["Lead Archivist"]
    assert manager.get_active_agents() == []

    assert manager.delete_agent(agent.id) is True
    assert manager.get_agent(agent.id) is None


def test_create_from_template_clones_template_values(tmp_path):
    manager = CustomAgentManager(tmp_path)

    clone = manager.create_from_template("heart_writer", name="Heart Keeper")

    assert clone is not None
    assert clone.name == "Heart Keeper"
    assert "Emotional truth" in clone.specialty
    assert clone.id != "tmpl_heart"


def test_custom_agent_rejects_blank_or_path_like_names():
    with pytest.raises(ValueError, match="Agent name is required"):
        CustomAgent(
            id="",
            name="   ",
            specialty="Continuity",
            guidance="Keep it steady.",
        )

    with pytest.raises(ValueError, match="path separators"):
        CustomAgent(
            id="",
            name="bad/name",
            specialty="Continuity",
            guidance="Keep it steady.",
        )


def test_custom_agent_manager_rejects_duplicate_names(tmp_path):
    manager = CustomAgentManager(tmp_path)
    manager.save_agent(
        CustomAgent(
            id="",
            name="Archivist",
            specialty="Continuity",
            guidance="Keep it steady.",
        )
    )

    with pytest.raises(ValueError, match="already exists"):
        manager.save_agent(
            CustomAgent(
                id="",
                name="Archivist",
                specialty="Foreshadowing",
                guidance="Plant the seed.",
            )
        )


def test_custom_agent_save_uses_atomic_replace(monkeypatch, tmp_path):
    agent = CustomAgent(
        id="",
        name="Archivist",
        specialty="Continuity and callbacks",
        guidance="Keep the story coherent.",
    )
    replace_calls: list[tuple[Path, Path]] = []
    real_replace = custom_agents_module.os.replace

    def tracking_replace(src, dst):
        replace_calls.append((Path(src), Path(dst)))
        return real_replace(src, dst)

    monkeypatch.setattr(custom_agents_module.os, "replace", tracking_replace)

    saved_path = Path(agent.save(tmp_path))

    assert replace_calls
    src, dst = replace_calls[0]
    assert src.name.endswith(".json.tmp")
    assert dst == saved_path
    assert not src.exists()
