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


def test_story_state_tracks_needs_threads_and_resolution():
    state = StoryState(premise="A town forgets its own mayor.")

    assert "Introduce a compelling character" in state.get_story_needs()

    state.add_character("Mara", "protagonist", "Find the missing records")
    state.add_plot_thread("records", "The missing archive ledgers", "Rod Serling", tension=7)

    active_threads = state.get_active_threads()
    assert len(active_threads) == 1
    assert active_threads[0].description == "The missing archive ledgers"

    state.resolve_plot_thread("records")
    assert state.get_active_threads() == []
