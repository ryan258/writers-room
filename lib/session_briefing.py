"""
Session briefing helpers built on the reusable executive_reporting component.
"""

from __future__ import annotations

from datetime import datetime
import html
from pathlib import Path
from typing import Any

from lib.personalities import STORY_MODES, is_dnd_mode


def render_session_brief(
    *,
    prompt: str,
    mode: str,
    story_state: Any,
    conversation_history: list[dict[str, Any]],
    leaderboard: list[dict[str, Any]],
    transcript_path: str | None = None,
    output_path: str | Path | None = None,
) -> str | None:
    """Render a reusable session brief to HTML and return the saved path."""
    try:
        from executive_reporting import (
            ExecutiveBrief,
            ExecutiveBriefingComponent,
            MinimalNarrativePlugin,
        )
    except ImportError:
        return _render_minimal_session_brief(
            prompt=prompt,
            mode=mode,
            story_state=story_state,
            conversation_history=conversation_history,
            leaderboard=leaderboard,
            transcript_path=transcript_path,
            output_path=output_path,
        )

    safe_prompt = _clean_text(prompt) or "Untitled Session"
    latest_messages = _latest_contributions(conversation_history)
    active_threads = list(story_state.get_active_threads()) if story_state else []
    story_needs = list(story_state.get_story_needs()) if story_state else []
    mode_info = STORY_MODES.get(mode, {})
    document_label = "Campaign Debrief" if is_dnd_mode(mode) else "Session Debrief"
    mode_name = mode_info.get("name", mode.upper())
    primary_need = _select_primary_need(mode, story_needs)

    headline = _build_headline(mode_name, story_state, active_threads)
    insight = _build_governing_insight(mode_name, story_state, active_threads, leaderboard)
    recommendations = _build_recommendations(mode, primary_need, active_threads, leaderboard)

    brief = ExecutiveBrief(
        brief_id=_slugify(f"{mode}-{safe_prompt}")[:64],
        title=f"{document_label}: {safe_prompt}",
        subtitle=mode_name,
        kicker=document_label,
        organization="Writers Room",
        publication_label="Collaborative Session Artifact",
        date_label=datetime.now().strftime("%B %d, %Y"),
        headline=headline,
        governing_question=_build_governing_question(mode),
        governing_insight=insight,
        executive_summary=_build_summary(
            mode=mode,
            mode_name=mode_name,
            story_state=story_state,
            primary_need=primary_need,
            active_threads=active_threads,
            latest_messages=latest_messages,
        ),
        top_metrics=_build_metrics(mode, story_state, conversation_history, leaderboard, active_threads),
        key_findings=_build_findings(latest_messages, active_threads, leaderboard),
        decision_implications=_build_implications(primary_need, active_threads, leaderboard),
        recommendations=recommendations,
        methodology=[
            "Brief generated from the shared story state and the final session transcript.",
            "Recent contributions were trimmed into recap findings to keep the artifact readable.",
        ],
        limitations=[
            "This recap is heuristic; it does not perform semantic summarization beyond the session state already tracked.",
        ],
        sources=_build_sources(transcript_path, latest_messages),
    )

    component = ExecutiveBriefingComponent(
        plugin=MinimalNarrativePlugin(document_label=document_label)
    )
    html_output = component.render_html(brief)

    target_path = _resolve_output_path(output_path, transcript_path)
    if target_path is None:
        return None

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(html_output, encoding="utf-8")
    return str(target_path)


def _render_minimal_session_brief(
    *,
    prompt: str,
    mode: str,
    story_state: Any,
    conversation_history: list[dict[str, Any]],
    leaderboard: list[dict[str, Any]],
    transcript_path: str | None = None,
    output_path: str | Path | None = None,
) -> str | None:
    """Fallback HTML brief when the optional executive_reporting package is unavailable."""
    safe_prompt = _clean_text(prompt) or "Untitled Session"
    all_contributions = _latest_contributions(conversation_history, limit=0)
    active_threads = list(story_state.get_active_threads()) if story_state else []
    story_needs = list(story_state.get_story_needs()) if story_state else []
    mode_info = STORY_MODES.get(mode, {})
    dnd = is_dnd_mode(mode)
    document_label = "Campaign Debrief" if dnd else "Session Debrief"
    mode_name = mode_info.get("name", mode.upper())
    primary_need = _select_primary_need(mode, story_needs)
    summary = _build_summary(
        mode=mode,
        mode_name=mode_name,
        story_state=story_state,
        primary_need=primary_need,
        active_threads=active_threads,
        latest_messages=all_contributions,
    )

    summary_items = "".join(f"<li>{html.escape(line)}</li>" for line in summary)

    # --- Build the full encounter / contributions log ---
    encounter_html = _build_encounter_log_html(conversation_history, dnd)

    # --- Leaderboard ---
    leaderboard_rows = "".join(
        f"<tr><td>{html.escape(item['name'])}</td>"
        f"<td>{item['average']}/10</td>"
        f"<td>{', '.join(str(s) for s in item.get('scores', []))}</td></tr>"
        for item in leaderboard
    )
    leaderboard_html = (
        f"<table><thead><tr><th>Agent</th><th>Average</th><th>Round Scores</th></tr></thead>"
        f"<tbody>{leaderboard_rows}</tbody></table>"
        if leaderboard_rows
        else "<p>No scores recorded.</p>"
    )
    if leaderboard:
        leader = leaderboard[0]
        leaderboard_html = (
            f"<p class=\"leader\">{html.escape(leader['name'])} led the table at {leader['average']}/10 average.</p>"
            + leaderboard_html
        )

    # --- Open Threads ---
    thread_items = "".join(
        f"<li>{html.escape(_clean_text(thread.description))}</li>"
        for thread in active_threads
    ) or "<li>No active threads remained.</li>"

    transcript_line = (
        f"<p class=\"transcript-link\">Full transcript: <code>{html.escape(transcript_path)}</code></p>"
        if transcript_path
        else ""
    )

    html_output = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(document_label)}: {html.escape(safe_prompt)}</title>
  <style>
    :root {{ --bg: #121212; --surface: #1A1A1A; --border: #242424; --text: #EBD2BE; --muted: #6B7280; --accent: #A6ACCD; }}
    body {{ margin: 0; font-family: Georgia, serif; background: var(--bg); color: var(--text); }}
    main {{ max-width: 960px; margin: 0 auto; padding: 32px 20px 56px; }}
    section {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px; margin-top: 20px; }}
    h1 {{ font-size: 1.7rem; margin: 4px 0 6px; }}
    h2 {{ font-size: 1.2rem; margin: 0 0 14px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }}
    h3 {{ font-size: 1rem; color: var(--accent); margin: 20px 0 10px; }}
    h3:first-child {{ margin-top: 0; }}
    p, li {{ line-height: 1.7; }}
    ul {{ margin: 0; padding-left: 20px; }}
    .eyebrow {{ color: var(--accent); text-transform: uppercase; letter-spacing: 0.14em; font-size: 0.75rem; }}
    .meta {{ color: var(--muted); font-size: 0.9rem; }}
    .hook {{ font-style: italic; color: var(--accent); margin: 12px 0; font-size: 1.05rem; }}
    .turn {{ margin: 8px 0; padding: 6px 0; }}
    .turn .agent-name {{ font-weight: bold; }}
    .turn .content {{ margin-left: 4px; }}
    .leader {{ font-size: 1.05rem; margin-bottom: 12px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.92rem; }}
    th, td {{ text-align: left; padding: 6px 10px; border-bottom: 1px solid var(--border); }}
    th {{ color: var(--accent); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; }}
    .transcript-link {{ color: var(--muted); font-size: 0.85rem; margin-top: 16px; }}
    code {{ background: var(--bg); padding: 2px 6px; border-radius: 4px; font-size: 0.85rem; }}
  </style>
</head>
<body>
  <main>
    <div class="eyebrow">Writers Room</div>
    <h1>{html.escape(document_label)}</h1>
    <p class="hook">{html.escape(safe_prompt)}</p>
    <p class="meta">{html.escape(mode_name)} &middot; {datetime.now().strftime("%B %d, %Y")}</p>
    <section>
      <h2>Summary</h2>
      <ul>{summary_items}</ul>
    </section>
    <section>
      <h2>{"Encounter Log" if dnd else "Session Log"}</h2>
      {encounter_html}
    </section>
    <section>
      <h2>Open Threads</h2>
      <ul>{thread_items}</ul>
    </section>
    <section>
      <h2>Leaderboard</h2>
      {leaderboard_html}
    </section>
    {transcript_line}
  </main>
</body>
</html>"""

    target_path = _resolve_output_path(output_path, transcript_path)
    if target_path is None:
        return None

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(html_output, encoding="utf-8")
    return str(target_path)
def _build_governing_question(mode: str) -> str:
    if is_dnd_mode(mode):
        return "What changed at the table, what pressure remains, and what should the party answer next?"
    return "What did the session establish, and where should the next pass concentrate?"


def _build_headline(mode_name: str, story_state: Any, active_threads: list[Any]) -> str:
    if not story_state:
        return f"{mode_name} session recap"

    if active_threads:
        thread = _clean_text(active_threads[0].description)
        return (
            f"{mode_name} session ended in {story_state.current_act.name.lower()} "
            f"with {thread.lower()} still unresolved."
        )

    return (
        f"{mode_name} session reached {story_state.current_act.name.lower()} "
        f"with tension at {story_state.tension_level}/10."
    )


def _build_governing_insight(
    mode_name: str,
    story_state: Any,
    active_threads: list[Any],
    leaderboard: list[dict[str, Any]],
) -> str:
    if not story_state:
        return f"{mode_name} session completed without enough shared state to produce a sharper recap."

    winner = leaderboard[0]["name"] if leaderboard else "the table"
    if active_threads:
        return (
            f"The session pushed {winner} toward the center of the action while leaving "
            f"{_clean_text(active_threads[0].description).lower()} as the next decisive pressure point."
        )
    return (
        f"The table advanced the scenario into {story_state.current_act.name.lower()} "
        f"with {winner} setting the clearest momentum."
    )


def _build_summary(
    *,
    mode: str,
    mode_name: str,
    story_state: Any,
    primary_need: str,
    active_threads: list[Any],
    latest_messages: list[dict[str, str]],
) -> list[str]:
    if not story_state:
        return [f"{mode_name} session completed, but the shared story state was unavailable for recap."]

    summary = [
        (
            f"{mode_name} session progressed through {story_state.round_count} rounds and "
            f"closed in {story_state.current_act.name.lower()} with tension at {story_state.tension_level}/10."
        )
    ]

    if is_dnd_mode(mode):
        summary.append(
            "The table was run as a level 9 D&D 2024 party with a dedicated Dungeon Master and magic-item loadouts capped at common, uncommon, and rare."
        )

    if latest_messages:
        summary.append(
            f"Most recent beat: {_clean_text(latest_messages[-1]['content'])}"
        )

    if active_threads:
        summary.append(
            f"Open pressure remains around {_clean_text(active_threads[0].description).lower()}."
        )
    elif primary_need:
        summary.append(f"Next pressure point: {_clean_text(primary_need)}.")

    return summary[:3]


def _build_metrics(
    mode: str,
    story_state: Any,
    conversation_history: list[dict[str, Any]],
    leaderboard: list[dict[str, Any]],
    active_threads: list[Any],
) -> list[Any]:
    from executive_reporting import EvidenceMetric

    round_count = getattr(story_state, "round_count", 0) or _infer_round_count(conversation_history)
    participant_count = len({msg.get("name") for msg in conversation_history if msg.get("name")})
    metrics = [
        EvidenceMetric(label="Mode", value=STORY_MODES.get(mode, {}).get("name", mode.upper()), source="Session config"),
        EvidenceMetric(label="Rounds", value=str(round_count), source="Story state"),
        EvidenceMetric(label="Participants", value=str(participant_count), source="Transcript"),
        EvidenceMetric(
            label="Word Count",
            value=str(getattr(story_state, "word_count", 0)),
            source="Story state",
        ),
    ]

    if active_threads:
        metrics.append(
            EvidenceMetric(
                label="Active Threads",
                value=str(len(active_threads)),
                source="Story state",
            )
        )

    if leaderboard:
        winner = leaderboard[0]
        metrics.append(
            EvidenceMetric(
                label="Top Score",
                value=f"{winner['average']}/10",
                source=winner["name"],
            )
        )

    return metrics[:6]


def _build_findings(
    latest_messages: list[dict[str, str]],
    active_threads: list[Any],
    leaderboard: list[dict[str, Any]],
) -> list[Any]:
    from executive_reporting import BriefFinding

    findings: list[Any] = []

    if latest_messages:
        recent = latest_messages[-1]
        findings.append(
            BriefFinding(
                title="Latest Beat",
                claim=_clean_text(recent["content"]),
                evidence_points=[
                    f"{item['name']}: {_clean_text(item['content'])}"
                    for item in latest_messages[-3:]
                ],
                implication="The next scene should answer or escalate this move.",
                confidence="directional",
            )
        )

    if active_threads:
        findings.append(
            BriefFinding(
                title="Primary Open Thread",
                claim=_clean_text(active_threads[0].description),
                evidence_points=[
                    f"Tension: {thread.tension_level}/10 | Status: {thread.status}"
                    for thread in active_threads[:2]
                ],
                implication="The unresolved thread should anchor the next round or next session.",
                confidence="medium",
            )
        )

    if leaderboard:
        winner = leaderboard[0]
        findings.append(
            BriefFinding(
                title="Standout Contributor",
                claim=f"{winner['name']} led the table at {winner['average']}/10 average.",
                evidence_points=[f"Round scores: {', '.join(str(score) for score in winner['scores'])}"],
                implication="That voice or role can carry the opening momentum next time.",
                confidence="medium",
            )
        )

    return findings[:3]


def _build_implications(
    primary_need: str,
    active_threads: list[Any],
    leaderboard: list[dict[str, Any]],
) -> list[str]:
    implications: list[str] = []

    if primary_need:
        implications.append(_clean_text(primary_need))
    if active_threads:
        implications.append(
            f"Resolve or escalate {_clean_text(active_threads[0].description).lower()} before opening new threads."
        )
    if leaderboard:
        implications.append(
            f"Use {leaderboard[0]['name']}'s momentum as the cleanest handoff into the next beat."
        )

    if not implications:
        implications.append("Continue the session from the last strong beat rather than restarting the premise.")

    return implications[:3]


def _build_recommendations(
    mode: str,
    primary_need: str,
    active_threads: list[Any],
    leaderboard: list[dict[str, Any]],
) -> list[Any]:
    from executive_reporting import BriefRecommendation

    recommendations: list[Any] = []

    if is_dnd_mode(mode):
        recommendations.append(
            BriefRecommendation(
                action="Open the next round with a hard consequence or a tactical choice from the Dungeon Master.",
                owner="Dungeon Master",
                timeline="Next session",
                expected_impact="Keeps the table in live-play mode instead of drifting into passive narration.",
                key_risk="If the opening is too soft, the table will collapse back into generic scene-writing.",
            )
        )
        recommendations.append(
            BriefRecommendation(
                action="Have the party answer the strongest open thread with one coordinated plan before splitting focus.",
                owner="Party",
                timeline="Next session",
                expected_impact="Turns the recap into an actionable encounter objective.",
                key_risk="Too many simultaneous objectives will flatten stakes.",
            )
        )
    else:
        recommendations.append(
            BriefRecommendation(
                action="Start the next pass from the sharpest unresolved beat instead of resetting the premise.",
                owner="Writers Room",
                timeline="Next session",
                expected_impact="Preserves momentum and keeps the collaborative thread coherent.",
                key_risk="A fresh restart would discard the current act and tension profile.",
            )
        )

    if primary_need:
        recommendations.append(
            BriefRecommendation(
                action=_clean_text(primary_need),
                owner="Lead contributor",
                timeline="Next round",
                expected_impact="Addresses the clearest gap identified by the shared story state.",
                key_risk="Ignoring the current need will make the scene feel repetitive.",
            )
        )
    elif active_threads:
        recommendations.append(
            BriefRecommendation(
                action=f"Pressure {_clean_text(active_threads[0].description).lower()} until it either resolves or mutates.",
                owner="Next speaker",
                timeline="Next round",
                expected_impact="Gives the session a strong continuation point.",
                key_risk="Introducing a new thread too early will diffuse tension.",
            )
        )

    if leaderboard:
        recommendations.append(
            BriefRecommendation(
                action=f"Let {leaderboard[0]['name']} establish the first strong turn or reveal in the follow-up.",
                owner=leaderboard[0]["name"],
                timeline="Opening beat",
                expected_impact="Uses the highest-scoring voice to re-anchor tone quickly.",
                key_risk="Over-relying on one contributor can narrow the ensemble dynamic.",
            )
        )

    return recommendations[:3]


def _build_sources(transcript_path: str | None, latest_messages: list[dict[str, str]]) -> list[str]:
    sources = []
    if transcript_path:
        sources.append(f"Transcript: {transcript_path}")
    for item in latest_messages[-3:]:
        sources.append(f"{item['name']}: {_clean_text(item['content'])}")
    return sources


def _build_encounter_log_html(conversation_history: list[dict[str, Any]], dnd: bool) -> str:
    """Build the full round-by-round (or flat) HTML log of all contributions."""
    assistant_msgs = [
        msg for msg in conversation_history
        if msg.get("role") == "assistant" and msg.get("content")
    ]
    if not assistant_msgs:
        return "<p>No contributions were recorded.</p>"

    # Check if we have round metadata
    has_rounds = any(msg.get("round") for msg in assistant_msgs)

    if has_rounds:
        rounds: dict[int, list[dict[str, Any]]] = {}
        for msg in assistant_msgs:
            r = msg.get("round", 0)
            rounds.setdefault(r, []).append(msg)

        sections = []
        for round_num in sorted(rounds):
            label = f"Round {round_num}" if round_num else "Prologue"
            turns = "".join(
                f'<div class="turn"><span class="agent-name">{html.escape(msg.get("name", "Agent"))}</span>: '
                f'<span class="content">{html.escape(_clean_text(msg.get("content", "")))}</span></div>'
                for msg in rounds[round_num]
            )
            sections.append(f"<h3>{html.escape(label)}</h3>{turns}")
        return "\n".join(sections)

    # Flat list for non-round sessions
    turns = "".join(
        f'<div class="turn"><span class="agent-name">{html.escape(msg.get("name", "Agent"))}</span>: '
        f'<span class="content">{html.escape(_clean_text(msg.get("content", "")))}</span></div>'
        for msg in assistant_msgs
    )
    return turns


def _latest_contributions(conversation_history: list[dict[str, Any]], limit: int = 0) -> list[dict[str, str]]:
    contributions = [
        {
            "name": str(message.get("name") or "Agent"),
            "content": _clean_text(str(message.get("content") or "")),
        }
        for message in conversation_history
        if message.get("role") == "assistant" and message.get("content")
    ]
    if limit > 0:
        return contributions[-limit:]
    return contributions


def _resolve_output_path(output_path: str | Path | None, transcript_path: str | None) -> Path | None:
    if output_path is not None:
        return Path(output_path)
    if transcript_path is None:
        return None
    transcript = Path(transcript_path)
    return transcript.with_name(f"{transcript.stem}_brief.html")


def _infer_round_count(conversation_history: list[dict[str, Any]]) -> int:
    rounds = {message.get("round") for message in conversation_history if message.get("round")}
    return len(rounds)


def _select_primary_need(mode: str, story_needs: list[str]) -> str:
    if not story_needs:
        return ""

    skipped_needs = {
        "Introduce a compelling character",
        "Add another character for conflict/interaction",
    }
    if is_dnd_mode(mode):
        for need in story_needs:
            cleaned = _clean_text(need)
            if cleaned not in skipped_needs:
                return cleaned
        return ""

    return _clean_text(story_needs[0])


def _clean_text(text: str) -> str:
    return " ".join(text.split())


def _slugify(value: str) -> str:
    chars = [char.lower() if char.isalnum() else "-" for char in value]
    slug = "".join(chars)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")
