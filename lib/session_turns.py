"""
Shared turn-generation helpers for CLI and web sessions.
"""

from __future__ import annotations

import re
from typing import Any


GENERAL_META_MARKERS = (
    "we need to",
    "we have to",
    "i need to",
    "i must",
    "let's craft",
    "the prompt",
    "output only",
    "no meta",
    "build on what others wrote",
    "don't repeat what others wrote",
    "do not repeat what others wrote",
    "story needs",
    "the center table",
    "your specialty",
    "assistant:",
    "system prompt",
    "user prompt",
    "role reminder",
    "reply again",
    "i am to embody",
    "speak only as",
)

DND_META_MARKERS = GENERAL_META_MARKERS + (
    "max 110 words",
    "continue the scene",
    "okay, i am",
    "okay i am",
    "okay, if i am",
    "if i am to",
    "i am the dm",
    "we are the dm",
    "declare one concrete action",
    "declare one useful action",
    "in the voice of",
    "play style",
    "your loadout",
    "table rules",
    "d&d table state",
    "adventure hook:",
    "act:",
    "tension:",
    "since it's inspired by",
    "since it’s inspired by",
    "the tone should be",
)

DND_FALLBACKS = {
    "Dungeon Master": (
        "A hard metallic rhythm rolls through the chamber as the nearest exit grinds shut and something heavy shifts behind the far wall. "
        "The air turns cold enough to sting, and whatever has been stalking the party has decided to stop hiding. What do you do?"
    ),
    "Rod Serling": (
        "Cassian raises the rapier and says, \"If this place wants witnesses, let's disappoint it by surviving the testimony.\""
    ),
    "Stephen King": (
        "Mae leans into the danger with the greatsword up and says, \"I want the fastest route to whatever thinks it just cornered us.\""
    ),
    "H.P. Lovecraft": (
        "Nhalia studies the disturbance and mutters, \"That pattern is deliberate, and I would rather break the ritual before it learns our names.\""
    ),
    "Jorge Luis Borges": (
        "Ivo opens the grimoire and says, \"I am checking whether the room we entered is still the room currently surrounding us.\""
    ),
    "Robert Stack": (
        "Silas drops to a knee and says, \"I'm reading the pattern before anyone crosses it; traps this confident usually want to be understood too late.\""
    ),
    "RIP Tequila Bot": (
        "Brother Agave splashes holy water toward the threat and says, \"Let's find out whether evil hates blessings more than it hates being mocked.\""
    ),
}

GENERIC_FALLBACK = (
    "The pressure in the scene tightens, and somebody has to move before the room decides for them."
)


def clean_single_line(text: str) -> str:
    """Collapse whitespace for display-safe output."""
    return " ".join(text.split())


def looks_like_dnd_meta_response(text: str) -> bool:
    """Return True when a D&D turn looks like prompt leakage."""
    lowered = text.strip().lower()
    if not lowered:
        return True
    if lowered.startswith("[error:"):
        return False
    if lowered in {":", "-", "okay", "okay,"}:
        return True

    preview = lowered[:220]
    if re.search(r"\bround\s+\d+\b", preview):
        return True
    return any(preview.startswith(marker) or marker in preview for marker in DND_META_MARKERS)


def looks_like_story_meta_response(text: str) -> bool:
    """Return True when prose output looks like prompt leakage."""
    lowered = text.strip().lower()
    if not lowered:
        return True
    if lowered.startswith("[error:"):
        return False
    if lowered in {":", "-", "okay", "okay,"}:
        return True

    preview = lowered[:220]
    return any(preview.startswith(marker) or marker in preview for marker in GENERAL_META_MARKERS)


def _extract_story_fragment(text: str, *, dnd_mode: bool) -> str:
    quote_match = re.search(r'["“](.+)', text, re.DOTALL)
    if quote_match:
        return quote_match.group(1).strip().rstrip('"”')

    colon_match = re.search(r":\s+(.+)", text, re.DOTALL)
    if colon_match:
        candidate = colon_match.group(1).strip()
        if dnd_mode:
            if not looks_like_dnd_meta_response(candidate):
                return candidate.rstrip('"”')
        elif not looks_like_story_meta_response(candidate):
            return candidate.rstrip('"”')

    for chunk in re.split(r"\n+|(?<=[.!?])\s+", text):
        candidate = chunk.strip().strip(' "“”')
        if not candidate:
            continue
        if dnd_mode and not looks_like_dnd_meta_response(candidate):
            return candidate
        if not dnd_mode and not looks_like_story_meta_response(candidate):
            return candidate

    return text.strip()


def clean_dnd_table_talk(text: str) -> str:
    """Extract the playable D&D table talk from a noisy model response."""
    candidate = _extract_story_fragment(text, dnd_mode=True)
    cleaned = clean_single_line(candidate).strip(' "“”')
    if cleaned.lower().startswith("the dimlylit"):
        cleaned = cleaned.replace("dimlylit", "dimly lit", 1)
    return cleaned


def clean_story_contribution(text: str) -> str:
    """Extract in-world prose from a noisy model response."""
    if text.strip().startswith("[ERROR:"):
        return text.strip()
    candidate = _extract_story_fragment(text, dnd_mode=False)
    return clean_single_line(candidate).strip(' "“”')


def build_clean_dnd_history(conversation_history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove prompt leakage from prior assistant turns before the next D&D call."""
    if not conversation_history:
        return []

    cleaned_history = [conversation_history[0]]
    for msg in conversation_history[1:]:
        content = msg.get("content", "")
        if not content:
            continue
        if msg.get("role") == "assistant":
            cleaned = clean_dnd_table_talk(content)
            if not cleaned or looks_like_dnd_meta_response(cleaned):
                continue
            cleaned_msg = msg.copy()
            cleaned_msg["content"] = cleaned
            cleaned_history.append(cleaned_msg)
            continue
        cleaned_history.append(msg)

    original_prompt = cleaned_history[0]
    recent_messages = cleaned_history[-8:]
    return [original_prompt] + [
        msg for msg in recent_messages if msg.get("content") != original_prompt.get("content")
    ]


def build_dnd_story_context(
    story_manager: Any,
    conversation_history: list[dict[str, Any]],
    display_name: str,
    round_num: int,
) -> str:
    """Build the concise D&D context block used by the DM/player turns."""
    state = story_manager.get_state()
    active_threads = state.get_active_threads()
    clean_history = build_clean_dnd_history(conversation_history)
    recent_turns = [
        f"- {msg.get('name', 'Agent')}: {clean_single_line(msg.get('content', ''))[:140]}"
        for msg in clean_history
        if msg.get("role") == "assistant" and msg.get("content")
    ][-3:]

    lines = [
        "=== D&D TABLE STATE ===",
        f"Adventure Hook: {state.premise}",
        f"Round: {round_num}",
        f"Act: {state.current_act.name}",
        f"Tension: {state.tension_level}/10",
    ]

    if active_threads:
        lines.append(f"Active Pressure: {clean_single_line(active_threads[0].description)}")
    else:
        lines.append("Active Pressure: The table needs one concrete problem, mystery, or threat.")

    if recent_turns:
        lines.append("Recent Table Talk:")
        lines.extend(recent_turns)

    if display_name == "Dungeon Master":
        lines.append(
            "Speak like the DM talking out loud at the table. Describe what the party perceives, then ask what they do."
        )
    else:
        lines.append(
            f"Speak like {display_name}'s player talking out loud at the table. Declare one immediate action, question, or line."
        )

    lines.append("No prompt talk. No explanation. No bullets.")
    lines.append("=" * 24)
    return "\n".join(lines)


def fallback_dnd_table_talk(display_name: str) -> str:
    """Return a mode-safe fallback line if the model keeps leaking instructions."""
    return DND_FALLBACKS.get(display_name, "I move before the silence turns into an ambush.")


def generate_dnd_turn(
    agent: Any,
    conversation_history: list[dict[str, Any]],
    story_context: str,
    display_name: str,
) -> str:
    """Generate a D&D turn with cleanup, retry, and fallback protection."""
    clean_history = build_clean_dnd_history(conversation_history)

    response = agent.generate_response(clean_history, story_context=story_context)
    cleaned = clean_dnd_table_talk(response)
    if cleaned and not looks_like_dnd_meta_response(cleaned):
        return cleaned

    correction = clean_history + [
        {
            "role": "user",
            "content": (
                f"Your last reply broke character. Reply again as {display_name} at the table right now. "
                "Start directly with the scene or action. Do not say 'Okay', 'I am', 'we need', or explain the prompt."
            ),
        }
    ]
    retry = agent.generate_response(correction, story_context=story_context)
    retry_cleaned = clean_dnd_table_talk(retry)
    if retry_cleaned and not looks_like_dnd_meta_response(retry_cleaned):
        return retry_cleaned

    return fallback_dnd_table_talk(display_name)


def generate_story_turn(
    agent: Any,
    conversation_history: list[dict[str, Any]],
    story_context: str,
    display_name: str,
) -> str:
    """Generate a fiction turn and strip out any prompt leakage before display."""
    response = agent.generate_response(conversation_history, story_context=story_context)
    cleaned = clean_story_contribution(response)
    if cleaned and not looks_like_story_meta_response(cleaned):
        return cleaned

    correction = conversation_history + [
        {
            "role": "user",
            "content": (
                f"Your last reply exposed instructions instead of story. Reply again as {display_name}. "
                "Output only the new in-world prose that advances the scene. No setup, no explanation, no bullets."
            ),
        }
    ]
    retry = agent.generate_response(correction, story_context=story_context)
    retry_cleaned = clean_story_contribution(retry)
    if retry_cleaned and not looks_like_story_meta_response(retry_cleaned):
        return retry_cleaned

    return GENERIC_FALLBACK
