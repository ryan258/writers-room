"""
Final-draft synthesis for Writers Room sessions.

After a non-D&D session finishes, the two-pass Editor runs a structural edit
followed by a line edit over the complete transcript to produce a single
publishable short story in Markdown.

The Editor is an opt-in feature: ``config['produce_final_draft']`` must be
truthy, and the session must not be in D&D mode.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .agents import Agent, coerce_agent_result
from .config import RuntimeConfig
from .personalities import (
    DEFAULT_MODEL,
    EDITOR_LINE,
    EDITOR_STRUCTURAL,
    build_final_draft_task,
)


def _assemble_transcript(conversation_history: List[Dict[str, Any]]) -> str:
    """Collect assistant contributions into a round-by-round transcript."""
    rounds: Dict[int, List[Dict[str, Any]]] = {}
    flat: List[Dict[str, Any]] = []
    for msg in conversation_history:
        if msg.get("role") != "assistant":
            continue
        if not msg.get("content"):
            continue
        round_num = msg.get("round") or 0
        if round_num:
            rounds.setdefault(round_num, []).append(msg)
        else:
            flat.append(msg)

    lines: List[str] = []
    for round_num in sorted(rounds):
        lines.append(f"=== Round {round_num} ===")
        for msg in rounds[round_num]:
            name = msg.get("name") or "Agent"
            lines.append(f"{name}: {msg['content'].strip()}")
        lines.append("")

    for msg in flat:
        name = msg.get("name") or "Agent"
        lines.append(f"{name}: {msg['content'].strip()}")

    return "\n".join(lines).strip()


def _strip_markdown_fences(text: str) -> str:
    """Remove accidental ```markdown fences if the editor wraps the output."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        first_newline = cleaned.find("\n")
        if first_newline != -1:
            cleaned = cleaned[first_newline + 1 :]
        if cleaned.rstrip().endswith("```"):
            cleaned = cleaned.rstrip()[:-3]
    return cleaned.strip()


def generate_final_draft(
    *,
    config: Dict[str, Any],
    conversation_history: List[Dict[str, Any]],
    story_state: Any,
    emit: Callable[[str, Dict[str, Any]], None],
    runtime_config: Optional[RuntimeConfig] = None,
) -> Optional[str]:
    """Run two Editor passes over the session transcript and return Markdown.

    Returns ``None`` if the transcript is empty or either pass fails. Failure
    modes are surfaced to the caller as ``error`` events via ``emit``.
    """
    transcript = _assemble_transcript(conversation_history)
    if not transcript:
        return None

    premise = config.get("prompt") or ""
    notes = config.get("notes") or ""
    mode = config.get("mode") or "horror"
    model = config.get("model") or DEFAULT_MODEL

    # ------------------------------------------------------------------
    # Pass 1 — Structural Editor
    # ------------------------------------------------------------------
    emit("editor_thinking", {"stage": "structural"})
    try:
        structural_agent = Agent(
            name="Structural Editor",
            model=model,
            system_prompt=EDITOR_STRUCTURAL,
            temperature=0.6,
            max_tokens=6000,
            window_size=1,
            runtime_config=runtime_config,
        )
        structural_task = build_final_draft_task(
            mode=mode,
            premise=premise,
            notes=notes,
            transcript=transcript,
            stage="structural",
        )
        structural_result = coerce_agent_result(
            structural_agent.generate_response(
                [{"role": "user", "content": structural_task}]
            )
        )
    except Exception as exc:  # pragma: no cover - defensive
        emit("error", {"message": f"Structural editor failed: {exc}"})
        return None

    if not structural_result.ok:
        emit(
            "error",
            {"message": f"Structural editor failed: {structural_result.error}"},
        )
        return None

    structural_raw = structural_result.content.strip()
    if not structural_raw:
        emit(
            "error",
            {"message": f"Structural editor returned no draft: {structural_raw}"},
        )
        return None

    structural_draft = _strip_markdown_fences(structural_raw)

    emit(
        "editor_response",
        {
            "stage": "structural",
            "preview": structural_draft[:240],
            "length": len(structural_draft),
        },
    )

    # ------------------------------------------------------------------
    # Pass 2 — Line Editor
    # ------------------------------------------------------------------
    emit("editor_thinking", {"stage": "line"})
    try:
        line_agent = Agent(
            name="Line Editor",
            model=model,
            system_prompt=EDITOR_LINE,
            temperature=0.5,
            max_tokens=6000,
            window_size=1,
            runtime_config=runtime_config,
        )
        line_task = build_final_draft_task(
            mode=mode,
            premise=premise,
            notes=notes,
            transcript=transcript,
            stage="line",
            previous=structural_draft,
        )
        line_result = coerce_agent_result(
            line_agent.generate_response(
                [{"role": "user", "content": line_task}]
            )
        )
    except Exception as exc:  # pragma: no cover - defensive
        emit("error", {"message": f"Line editor failed: {exc}"})
        return None

    if not line_result.ok:
        emit("error", {"message": f"Line editor failed: {line_result.error}"})
        return None

    line_raw = line_result.content.strip()
    if not line_raw:
        emit(
            "error",
            {"message": f"Line editor returned no draft: {line_raw}"},
        )
        return None

    final_draft = _strip_markdown_fences(line_raw)

    emit(
        "editor_response",
        {
            "stage": "line",
            "preview": final_draft[:240],
            "length": len(final_draft),
        },
    )

    return final_draft
