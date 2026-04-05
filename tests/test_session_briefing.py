import html
from pathlib import Path

from lib.session_briefing import render_session_brief
from lib.story_state import StoryStateManager


def test_render_session_brief_creates_dnd_campaign_artifact(tmp_path):
    manager = StoryStateManager(
        premise="Recover the ember crown from the drowned keep.",
        mode="dnd",
    )
    manager.process_contribution(
        "Black water climbs the chapel steps as the drowned keep exhales and the relic glows under the altar.",
        "Dungeon Master",
        1,
    )
    manager.process_contribution(
        "Cassian raises the Cli Lyre and bargains for one minute of truth before anyone draws steel.",
        "Rod Serling",
        1,
    )
    manager.process_contribution(
        "Mae plants the flame tongue in the stone and dares the thing beneath the altar to come claim it.",
        "Stephen King",
        1,
    )

    conversation_history = [
        {
            "role": "user",
            "content": "Run a Dungeons & Dragons 2024 (5.5) session for this hook.",
        },
        {
            "role": "assistant",
            "name": "Dungeon Master",
            "content": "Black water climbs the chapel steps as the drowned keep exhales and the relic glows under the altar.",
        },
        {
            "role": "assistant",
            "name": "Rod Serling",
            "content": "Cassian raises the Cli Lyre and bargains for one minute of truth before anyone draws steel.",
        },
        {
            "role": "assistant",
            "name": "Stephen King",
            "content": "Mae plants the flame tongue in the stone and dares the thing beneath the altar to come claim it.",
        },
    ]

    output_path = tmp_path / "campaign_brief.html"
    brief_path = render_session_brief(
        prompt="Recover the ember crown from the drowned keep.",
        mode="dnd",
        story_state=manager.state,
        conversation_history=conversation_history,
        leaderboard=[
            {"name": "Dungeon Master", "average": 8.5, "scores": [8, 9]},
            {"name": "Rod Serling", "average": 8.0, "scores": [8]},
        ],
        output_path=output_path,
    )

    assert brief_path == str(output_path)
    rendered = Path(brief_path).read_text(encoding="utf-8")
    unescaped = html.unescape(rendered)
    assert "Campaign Debrief" in rendered
    assert "Recover the ember crown from the drowned keep." in rendered
    assert "level 9 D&D 2024 party" in unescaped
    assert "Dungeon Master led the table at 8.5/10 average." in unescaped
