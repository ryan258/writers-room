import html
from pathlib import Path

from lib.session_briefing import _final_draft_to_html, render_session_brief
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


def test_final_draft_to_html_keeps_prose_after_headings():
    """A heading followed by prose in the same block must preserve the prose."""
    markdown = (
        "# The Closet\n"
        "A quiet room with a door that did not belong.\n\n"
        "## Scene One\n"
        "The floorboards breathed once, then fell still.\n"
        "The lamp refused to turn on.\n\n"
        "Just a plain paragraph on its own."
    )

    html_output = _final_draft_to_html(markdown)

    assert "<h1>The Closet</h1>" in html_output
    assert "<h2>Scene One</h2>" in html_output
    # Prose directly under the H1 must not be dropped.
    assert "A quiet room with a door that did not belong." in html_output
    # Multi-line prose directly under the H2 must be preserved.
    assert "The floorboards breathed once, then fell still." in html_output
    assert "The lamp refused to turn on." in html_output
    # Standalone paragraph still renders.
    assert "<p>Just a plain paragraph on its own.</p>" in html_output


def test_final_draft_to_html_escapes_and_ignores_inline_markup():
    """HTML in prose is escaped; heading parsing does not leak markup."""
    markdown = "## A <script>alert(1)</script>\nStay safe."

    html_output = _final_draft_to_html(markdown)

    assert "<script>" not in html_output
    assert "&lt;script&gt;" in html_output
    assert "Stay safe." in html_output


def test_render_session_brief_embeds_final_draft_section(tmp_path):
    """A supplied final draft markdown appears as the headline section."""
    manager = StoryStateManager(
        premise="A locked closet hums at night.",
        mode="horror",
    )
    manager.process_contribution(
        "The nurse hears the walls breathing near the linen closet at 2:13 AM.",
        "Stephen King",
        1,
    )

    conversation_history = [
        {"role": "user", "content": "Write a scene about: A locked closet hums at night."},
        {
            "role": "assistant",
            "name": "Stephen King",
            "content": "The nurse hears the walls breathing near the linen closet at 2:13 AM.",
        },
    ]

    final_draft = (
        "# The Linen Closet\n"
        "She heard the hum first, then the steady rhythm behind it.\n\n"
        "## 2:13 AM\n"
        "The door was warm to the touch."
    )

    output_path = tmp_path / "final_brief.html"
    brief_path = render_session_brief(
        prompt="A locked closet hums at night.",
        mode="horror",
        story_state=manager.state,
        conversation_history=conversation_history,
        leaderboard=[],
        output_path=output_path,
        final_draft_markdown=final_draft,
    )

    assert brief_path == str(output_path)
    rendered = Path(brief_path).read_text(encoding="utf-8")
    assert "final-draft" in rendered
    assert "<h1>The Linen Closet</h1>" in rendered
    assert "She heard the hum first, then the steady rhythm behind it." in rendered
    assert "<h2>2:13 AM</h2>" in rendered
    assert "The door was warm to the touch." in rendered
