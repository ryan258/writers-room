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
