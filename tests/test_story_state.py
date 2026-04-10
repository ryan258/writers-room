from lib.story_state import StoryAct, StoryState, StoryStateManager


def test_story_state_manager_updates_tension_pacing_and_act():
    manager = StoryStateManager(premise="A cellar door hums at midnight.", mode="horror")

    manager.process_contribution("A scream tore through the house.", "Rod Serling", 1)
    assert manager.get_state().tension_level == 4
    assert manager.get_state().pacing == "fast"

    manager.process_contribution("Blood spread across the stairs.", "Stephen King", 2)
    manager.process_contribution("Terror settled into every room.", "Robert Stack", 3)

    assert manager.get_state().current_act == StoryAct.CONFRONTATION
    assert manager.get_state().round_count == 3


def test_story_state_context_and_payload_match_runtime_shape():
    state = StoryState(premise="A town forgets its own mayor.")

    assert state.get_story_needs() == ["Establish a concrete source of conflict or unease"]

    state.add_segment("The square bells ring with no one pulling the ropes.", "Rod Serling", 1)
    state.add_segment("The mayor's portrait has been painted over with an empty chair.", "Stephen King", 2)

    context = state.to_prompt_context()
    payload = state.to_dict()

    assert "CHARACTERS:" not in context
    assert "ACTIVE THREADS:" not in context
    assert "THEMES:" not in context
    assert "CURRENT FOCUS:" in context
    assert "story_segments" in payload
    assert "characters" not in payload
    assert "plot_threads" not in payload
    assert "themes" not in payload
