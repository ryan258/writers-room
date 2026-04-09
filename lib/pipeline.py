"""
Pipeline report generation for finalized drafts.

The pipeline produces a directory of artifacts for each final draft:

    pipelines/{title-slug}/
        status.md              # editing steps + polish checklist (1 JSON call)
        marketing/
            logline.md
            back-cover.md
            character-sheet.md
            pull-quotes.md
            cover-brief.md
            social-teasers.md
            newsletter.md
            landing-page.md
        index.md               # links + timestamps + pending markers
        .failures.json         # retry manifest (omitted when empty)

Each marketing asset gets its own model call with the full token budget, so
long-form copy (back-cover blurb, landing page) isn't starved by a shared
budget with the short-form items (logline, pull quotes).
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any, Iterable

from .agents import Agent
from .artifacts import (
    DEFAULT_PIPELINES_DIR,
    derive_pipeline_dirname_from_final_path,
    extract_markdown_title,
)
from .personalities import DEFAULT_MODEL


logger = logging.getLogger(__name__)


# Max concurrent marketing-asset calls. Kept low to avoid provider throttling.
MARKETING_BATCH_SIZE = 2

# Retry manifest filename, stored inside pipelines/{title}/
FAILURES_MANIFEST_NAME = ".failures.json"


EDITING_STEPS = [
    "Intake two-pass draft",
    "Structural read",
    "Scene reorder pass",
    "Continuity sweep",
    "Line edit",
    "Copy edit",
    "Proofread",
    "Final read-through",
]

POLISH_CHECKLIST = [
    "Consistent POV",
    "Tense check",
    "Dialogue tags trimmed",
    "Repetition flagged",
    "Sensory detail balance",
    "Pacing spot-checks",
    "Name/place spelling",
    "Formatting normalized",
]


@dataclass(frozen=True)
class MarketingAssetSpec:
    """Specification for a single marketing asset call."""
    slug: str              # filename stem, e.g. "logline"
    name: str              # display name, e.g. "Logline"
    filename: str          # full filename with extension
    system_prompt: str     # per-asset system prompt
    instructions: str      # per-asset user-message instructions
    max_tokens: int        # per-asset token budget


_MARKETING_BASE_RULES = (
    "Respect the draft as the source of truth. Do not invent plot points that are "
    "not supported by the draft. Write in plain Markdown. Do not wrap your response "
    "in code fences. Do not add a heading — the caller wraps the output."
)


MARKETING_ASSET_SPECS: list[MarketingAssetSpec] = [
    MarketingAssetSpec(
        slug="logline",
        name="Logline",
        filename="logline.md",
        system_prompt=(
            "You write loglines for finished fiction drafts. "
            "A great logline is one sentence, 25 words or fewer, with a clear "
            "protagonist, an inciting conflict, and stakes. " + _MARKETING_BASE_RULES
        ),
        instructions=(
            "Write a single-sentence logline for this draft. "
            "Keep it under 25 words. Return only the sentence."
        ),
        max_tokens=200,
    ),
    MarketingAssetSpec(
        slug="back-cover",
        name="Back-cover blurb",
        filename="back-cover.md",
        system_prompt=(
            "You write back-cover blurbs for finished fiction. A great blurb is "
            "three short paragraphs: the hook, the stakes, and the cliffhanger. "
            "Total length 100-150 words. " + _MARKETING_BASE_RULES
        ),
        instructions=(
            "Write a back-cover blurb for this draft. Three paragraphs, 100-150 "
            "words total, ending on a cliffhanger question or implication."
        ),
        max_tokens=600,
    ),
    MarketingAssetSpec(
        slug="character-sheet",
        name="Character one-sheet",
        filename="character-sheet.md",
        system_prompt=(
            "You write character one-sheets for finished fiction. Each profile "
            "is a Markdown section with the character name as a level-3 heading "
            "followed by three short lines: Role, Want, Wound. "
            + _MARKETING_BASE_RULES
        ),
        instructions=(
            "Identify the 2-3 most important characters in the draft and write a "
            "one-sheet for each. Use `### Name` as the heading, then three bullet "
            "lines prefixed `- Role:`, `- Want:`, `- Wound:`."
        ),
        max_tokens=800,
    ),
    MarketingAssetSpec(
        slug="pull-quotes",
        name="Pull quotes",
        filename="pull-quotes.md",
        system_prompt=(
            "You select pull quotes from finished fiction. Every quote must be "
            "taken verbatim from the draft, attributed to the narrator unless "
            "the draft makes the speaker unambiguous. " + _MARKETING_BASE_RULES
        ),
        instructions=(
            "Select 3-5 evocative pull quotes from the draft. Quote each on its "
            "own line as a Markdown blockquote. Do not paraphrase."
        ),
        max_tokens=500,
    ),
    MarketingAssetSpec(
        slug="cover-brief",
        name="Cover art brief",
        filename="cover-brief.md",
        system_prompt=(
            "You write cover art briefs for a designer who has not read the draft. "
            "You cover mood, palette, key imagery, focal subject, and symbolic "
            "elements. Do not specify fonts. " + _MARKETING_BASE_RULES
        ),
        instructions=(
            "Write a cover art brief in five short sections: **Mood**, **Palette**, "
            "**Focal Subject**, **Key Imagery**, **Symbolic Elements**. Each section "
            "is 1-3 sentences."
        ),
        max_tokens=700,
    ),
    MarketingAssetSpec(
        slug="social-teasers",
        name="Social teasers",
        filename="social-teasers.md",
        system_prompt=(
            "You write social media teasers for finished fiction. You optimize "
            "copy per platform: Twitter/X (under 250 chars), Instagram (caption "
            "with one hook line and a short body), BlueSky (under 300 chars). "
            + _MARKETING_BASE_RULES
        ),
        instructions=(
            "Write three distinct teasers as Markdown sections titled "
            "`### Twitter/X`, `### Instagram`, `### BlueSky`. Each section contains "
            "the ready-to-post copy only — no meta notes."
        ),
        max_tokens=700,
    ),
    MarketingAssetSpec(
        slug="newsletter",
        name="Newsletter snippet",
        filename="newsletter.md",
        system_prompt=(
            "You write author newsletter snippets announcing a new story. Voice is "
            "warm, direct, and second-person. Target length is 150-200 words. "
            + _MARKETING_BASE_RULES
        ),
        instructions=(
            "Write a newsletter snippet (150-200 words) that introduces the story, "
            "teases the hook, and ends with a clear call to read. Do not include a "
            "subject line."
        ),
        max_tokens=700,
    ),
    MarketingAssetSpec(
        slug="landing-page",
        name="Launch landing page",
        filename="landing-page.md",
        system_prompt=(
            "You write landing-page copy for the launch of a new short story. The "
            "page has a headline, a subhead, a 2-3 paragraph body, and a call to "
            "action. " + _MARKETING_BASE_RULES
        ),
        instructions=(
            "Write landing-page copy in four sections: `## Headline`, `## Subhead`, "
            "`## Body`, `## Call to Action`. Body is 2-3 short paragraphs. CTA is a "
            "single imperative button phrase."
        ),
        max_tokens=1200,
    ),
]

_SPEC_BY_SLUG: dict[str, MarketingAssetSpec] = {
    spec.slug: spec for spec in MARKETING_ASSET_SPECS
}


STATUS_SYSTEM_PROMPT = """You are the Pipeline Editor for a finished fiction draft.

You receive a finalized draft in Markdown. Your job is to evaluate the draft
against a fixed editing + polish pipeline and return structured JSON.

Rules:
1. Respect the draft as the source of truth.
2. Be specific and actionable.
3. Do not invent plot points that are not supported by the draft.
4. Use concise language.
5. Return JSON only.

Output schema:
{
  "editing_steps": [
    {
      "step": "Intake two-pass draft",
      "status": "complete|revise|blocked",
      "summary": "short summary",
      "next_action": "short action"
    }
  ],
  "polish_checklist": [
    {
      "item": "Consistent POV",
      "status": "pass|revise",
      "note": "short note"
    }
  ]
}
"""


# ---------------------------------------------------------------------------
# Status (editing + polish) call
# ---------------------------------------------------------------------------


def build_status_task(draft_markdown: str) -> str:
    """Build the user prompt for the status (editing + polish) call."""
    return (
        "Evaluate this final draft against the fixed editing and polish pipeline.\n\n"
        f"Editing steps: {EDITING_STEPS}\n"
        f"Polish checklist: {POLISH_CHECKLIST}\n\n"
        "For editing steps, mark `complete` only when the draft already satisfies the goal.\n"
        "Use `revise` when work remains and `blocked` only when the draft lacks the information needed.\n"
        "For the polish checklist, use `pass` or `revise`.\n\n"
        "Draft:\n"
        f"{draft_markdown}"
    )


def _normalize_status_data(raw: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    editing_items = raw.get("editing_steps") or []
    polish_items_raw = raw.get("polish_checklist") or []

    dropped_editing = {
        str(item.get("step", "")).strip()
        for item in editing_items
        if isinstance(item, dict)
    } - set(EDITING_STEPS)
    dropped_polish = {
        str(item.get("item", "")).strip()
        for item in polish_items_raw
        if isinstance(item, dict)
    } - set(POLISH_CHECKLIST)
    if dropped_editing or dropped_polish:
        logger.debug(
            "Dropped status keys: editing=%s polish=%s",
            sorted(name for name in dropped_editing if name),
            sorted(name for name in dropped_polish if name),
        )

    editing_by_name = {
        str(item.get("step", "")).strip(): item
        for item in editing_items
        if isinstance(item, dict)
    }
    polish_by_name = {
        str(item.get("item", "")).strip(): item
        for item in polish_items_raw
        if isinstance(item, dict)
    }

    editing_steps: list[dict[str, str]] = []
    for step in EDITING_STEPS:
        item = editing_by_name.get(step, {})
        status = str(item.get("status", "revise")).strip().lower()
        if status not in {"complete", "revise", "blocked"}:
            status = "revise"
        editing_steps.append(
            {
                "step": step,
                "status": status,
                "summary": str(item.get("summary", "")).strip(),
                "next_action": str(item.get("next_action", "")).strip(),
            }
        )

    polish_items: list[dict[str, str]] = []
    for item_name in POLISH_CHECKLIST:
        item = polish_by_name.get(item_name, {})
        status = str(item.get("status", "revise")).strip().lower()
        if status not in {"pass", "revise"}:
            status = "revise"
        polish_items.append(
            {
                "item": item_name,
                "status": status,
                "note": str(item.get("note", "")).strip(),
            }
        )

    return {
        "editing_steps": editing_steps,
        "polish_checklist": polish_items,
    }


def generate_status_data(
    *,
    draft_markdown: str,
    model: str = DEFAULT_MODEL,
) -> dict[str, list[dict[str, str]]]:
    """Generate structured editing + polish status from a final draft."""
    if not draft_markdown.strip():
        raise ValueError("Cannot generate pipeline from an empty draft.")

    # Status is a structured JSON call. Sixteen short items fit comfortably in
    # a smaller token budget than the marketing calls below.
    agent = Agent(
        name="Pipeline Editor",
        model=model,
        system_prompt=STATUS_SYSTEM_PROMPT,
        temperature=0.4,
        max_tokens=2500,
        window_size=1,
        response_format={"type": "json_object"},
    )
    raw_response = agent.generate_response(
        [{"role": "user", "content": build_status_task(draft_markdown)}]
    )
    try:
        parsed = json.loads(raw_response)
    except (TypeError, json.JSONDecodeError) as exc:
        logger.debug("Pipeline editor returned invalid JSON: %r", raw_response)
        raise ValueError("Pipeline editor returned invalid JSON.") from exc
    if not isinstance(parsed, dict) or not parsed:
        logger.debug("Pipeline editor returned invalid JSON payload: %r", parsed)
        raise ValueError("Pipeline editor returned invalid JSON.")
    return _normalize_status_data(parsed)


def render_status_markdown(
    *,
    title: str,
    draft_path: str | Path,
    status_data: dict[str, list[dict[str, str]]],
) -> str:
    """Render the status.md file for a pipeline directory."""
    editing_lines: list[str] = []
    for item in status_data["editing_steps"]:
        checkbox = "x" if item["status"] == "complete" else " "
        status = item["status"].upper()
        line = f"- [{checkbox}] {item['step']} ({status})"
        if item["summary"]:
            line += f": {item['summary']}"
        editing_lines.append(line)
        if item["next_action"]:
            editing_lines.append(f"  Next: {item['next_action']}")

    polish_lines: list[str] = []
    for item in status_data["polish_checklist"]:
        checkbox = "x" if item["status"] == "pass" else " "
        status = item["status"].upper()
        line = f"- [{checkbox}] {item['item']} ({status})"
        if item["note"]:
            line += f": {item['note']}"
        polish_lines.append(line)

    return "\n".join(
        [
            f"# {title} — Status",
            "",
            f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Source final draft: `{draft_path}`",
            "",
            "## Editing Steps",
            "",
            *editing_lines,
            "",
            "## Polish Checklist",
            "",
            *polish_lines,
            "",
        ]
    ).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Marketing asset calls
# ---------------------------------------------------------------------------


def generate_marketing_asset(
    *,
    spec: MarketingAssetSpec,
    draft_markdown: str,
    model: str = DEFAULT_MODEL,
) -> str:
    """Generate copy for a single marketing asset. Returns raw Markdown body."""
    if not draft_markdown.strip():
        raise ValueError("Cannot generate marketing asset from an empty draft.")

    agent = Agent(
        name=f"Marketing/{spec.name}",
        model=model,
        system_prompt=spec.system_prompt,
        temperature=0.6,
        max_tokens=spec.max_tokens,
        window_size=1,
    )
    user_message = (
        f"{spec.instructions}\n\nDraft:\n{draft_markdown}"
    )
    raw = agent.generate_response([{"role": "user", "content": user_message}])
    if not raw or not raw.strip():
        raise ValueError(f"Marketing asset '{spec.slug}' returned empty copy.")
    return raw.strip()


def render_marketing_asset_file(spec: MarketingAssetSpec, body: str) -> str:
    """Wrap a marketing asset body with a canonical file header."""
    return "\n".join(
        [
            f"# {spec.name}",
            "",
            f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            body.strip(),
            "",
        ]
    ).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Failures manifest
# ---------------------------------------------------------------------------


def _failures_manifest_path(pipeline_dir: Path) -> Path:
    return pipeline_dir / FAILURES_MANIFEST_NAME


def _write_failures_manifest(
    pipeline_dir: Path,
    *,
    draft_path: str,
    status_failed: bool,
    marketing_failed: Iterable[str],
) -> None:
    marketing_failed_list = sorted(set(marketing_failed))
    manifest_path = _failures_manifest_path(pipeline_dir)
    if not status_failed and not marketing_failed_list:
        if manifest_path.exists():
            manifest_path.unlink()
        return
    payload = {
        "draft_path": str(draft_path),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status_failed": status_failed,
        "marketing_failed": marketing_failed_list,
    }
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )


def _read_failures_manifest(pipeline_dir: Path) -> dict[str, Any] | None:
    manifest_path = _failures_manifest_path(pipeline_dir)
    if not manifest_path.exists():
        return None
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def get_pipeline_failures(pipeline_dir: str | Path) -> dict[str, Any] | None:
    """Return normalized failure state for a pipeline directory, if any."""
    manifest = _read_failures_manifest(Path(pipeline_dir))
    if not manifest:
        return None

    status_failed = bool(manifest.get("status_failed"))
    marketing_failed = sorted(set(manifest.get("marketing_failed") or []))
    if not status_failed and not marketing_failed:
        return None

    return {
        "status_failed": status_failed,
        "marketing_failed": marketing_failed,
        "draft_path": manifest.get("draft_path"),
        "generated_at": manifest.get("generated_at"),
    }


# ---------------------------------------------------------------------------
# Index rendering
# ---------------------------------------------------------------------------


def render_index_markdown(
    *,
    title: str,
    draft_path: str | Path,
    status_ok: bool,
    marketing_results: dict[str, dict[str, Any]],
) -> str:
    """Render index.md linking all generated artifacts and flagging failures."""
    lines = [
        f"# {title} — Pipeline",
        "",
        f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Source final draft: `{draft_path}`",
        "",
        "## Status",
        "",
    ]
    if status_ok:
        lines.append("- [x] [status.md](status.md)")
    else:
        lines.append("- [ ] status.md — PENDING (generation failed)")
    lines.extend(["", "## Marketing Assets", ""])
    for spec in MARKETING_ASSET_SPECS:
        result = marketing_results.get(spec.slug, {})
        if result.get("ok"):
            lines.append(f"- [x] [{spec.name}](marketing/{spec.filename})")
        else:
            reason = result.get("error") or "not generated"
            lines.append(
                f"- [ ] {spec.name} — PENDING ({reason})"
            )
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def _resolve_pipeline_dir(
    *,
    draft_path: Path,
    draft_markdown: str,
    output_dir: str | Path | None,
    pipelines_root: str | Path,
) -> tuple[Path, str]:
    """Return (pipeline_dir, title) for a draft."""
    title = extract_markdown_title(draft_markdown) or draft_path.stem.replace("_", " ")
    if output_dir is not None:
        return Path(output_dir), title
    pipeline_dirname = derive_pipeline_dirname_from_final_path(draft_path)
    return Path(pipelines_root) / pipeline_dirname, title


def _run_marketing_batch(
    specs: list[MarketingAssetSpec],
    *,
    draft_markdown: str,
    model: str,
    pipeline_dir: Path,
) -> dict[str, dict[str, Any]]:
    """Run marketing asset calls in batches of MARKETING_BATCH_SIZE."""
    marketing_dir = pipeline_dir / "marketing"
    marketing_dir.mkdir(parents=True, exist_ok=True)

    results: dict[str, dict[str, Any]] = {}
    if not specs:
        return results

    with ThreadPoolExecutor(max_workers=MARKETING_BATCH_SIZE) as executor:
        future_to_spec = {
            executor.submit(
                generate_marketing_asset,
                spec=spec,
                draft_markdown=draft_markdown,
                model=model,
            ): spec
            for spec in specs
        }
        for future in as_completed(future_to_spec):
            spec = future_to_spec[future]
            try:
                body = future.result()
                rendered = render_marketing_asset_file(spec, body)
                (marketing_dir / spec.filename).write_text(rendered, encoding="utf-8")
                results[spec.slug] = {"ok": True, "path": str(marketing_dir / spec.filename)}
            except Exception as exc:  # noqa: BLE001 — partial failures are fine
                logger.warning("Marketing asset %s failed: %s", spec.slug, exc)
                results[spec.slug] = {"ok": False, "error": str(exc)}
    return results


def generate_pipeline_report_from_draft(
    *,
    draft_path: str | Path,
    model: str = DEFAULT_MODEL,
    output_dir: str | Path | None = None,
    pipelines_root: str | Path = DEFAULT_PIPELINES_DIR,
    only_slugs: Iterable[str] | None = None,
    include_status: bool = True,
) -> str:
    """Read a final draft, generate the pipeline directory, and return its path.

    Parameters
    ----------
    draft_path:
        Path to the finalized draft Markdown file.
    model:
        Model override for both status and marketing calls.
    output_dir:
        Explicit target directory. When omitted, defaults to
        ``pipelines_root / {title-slug}``.
    pipelines_root:
        Root pipelines directory used when ``output_dir`` is not given.
    only_slugs:
        Optional iterable of marketing-asset slugs to regenerate. When set,
        other assets are left alone and the status call is controlled by
        ``include_status``. Used by ``retry_failed_pipeline_items``.
    include_status:
        When ``False``, skip the status call (retry flows set this).
    """
    draft_file = Path(draft_path)
    draft_markdown = draft_file.read_text(encoding="utf-8")

    pipeline_dir, title = _resolve_pipeline_dir(
        draft_path=draft_file,
        draft_markdown=draft_markdown,
        output_dir=output_dir,
        pipelines_root=pipelines_root,
    )
    pipeline_dir.mkdir(parents=True, exist_ok=True)

    # ---- Status (editing + polish) ----
    status_ok = True
    if include_status:
        try:
            status_data = generate_status_data(
                draft_markdown=draft_markdown, model=model
            )
            status_markdown = render_status_markdown(
                title=title, draft_path=draft_file, status_data=status_data
            )
            (pipeline_dir / "status.md").write_text(
                status_markdown, encoding="utf-8"
            )
        except Exception as exc:  # noqa: BLE001 — partial failures are fine
            logger.warning("Pipeline status generation failed: %s", exc)
            status_ok = False
    else:
        # Inherit prior status file state if present.
        status_ok = (pipeline_dir / "status.md").exists()

    # ---- Marketing assets (batched parallel) ----
    if only_slugs is None:
        selected_specs = list(MARKETING_ASSET_SPECS)
    else:
        slug_set = set(only_slugs)
        unknown = slug_set - set(_SPEC_BY_SLUG)
        if unknown:
            logger.warning("Ignoring unknown marketing asset slugs: %s", sorted(unknown))
        selected_specs = [
            _SPEC_BY_SLUG[slug] for slug in slug_set if slug in _SPEC_BY_SLUG
        ]

    new_results = _run_marketing_batch(
        selected_specs,
        draft_markdown=draft_markdown,
        model=model,
        pipeline_dir=pipeline_dir,
    )

    # Merge with any pre-existing assets on disk so index.md and the failures
    # manifest reflect the full state (not just what we regenerated this run).
    marketing_results: dict[str, dict[str, Any]] = {}
    marketing_dir = pipeline_dir / "marketing"
    for spec in MARKETING_ASSET_SPECS:
        if spec.slug in new_results:
            marketing_results[spec.slug] = new_results[spec.slug]
            continue
        existing = marketing_dir / spec.filename
        if existing.exists():
            marketing_results[spec.slug] = {"ok": True, "path": str(existing)}
        else:
            marketing_results[spec.slug] = {"ok": False, "error": "not generated"}

    # ---- Index + failures manifest ----
    index_markdown = render_index_markdown(
        title=title,
        draft_path=draft_file,
        status_ok=status_ok,
        marketing_results=marketing_results,
    )
    (pipeline_dir / "index.md").write_text(index_markdown, encoding="utf-8")

    failed_marketing = [
        slug for slug, result in marketing_results.items() if not result.get("ok")
    ]
    _write_failures_manifest(
        pipeline_dir,
        draft_path=str(draft_file),
        status_failed=not status_ok,
        marketing_failed=failed_marketing,
    )

    if not status_ok or failed_marketing:
        logger.info(
            "Pipeline generated with failures: status_failed=%s marketing_failed=%s",
            not status_ok,
            failed_marketing,
        )

    return str(pipeline_dir)


def retry_failed_pipeline_items(
    *,
    draft_path: str | Path,
    model: str = DEFAULT_MODEL,
    output_dir: str | Path | None = None,
    pipelines_root: str | Path = DEFAULT_PIPELINES_DIR,
) -> str:
    """Retry only items listed in ``.failures.json`` for this draft.

    If no manifest exists (or it's empty), this is a no-op and returns the
    existing pipeline directory path.
    """
    draft_file = Path(draft_path)
    draft_markdown = draft_file.read_text(encoding="utf-8")

    pipeline_dir, _title = _resolve_pipeline_dir(
        draft_path=draft_file,
        draft_markdown=draft_markdown,
        output_dir=output_dir,
        pipelines_root=pipelines_root,
    )

    manifest = _read_failures_manifest(pipeline_dir)
    if not manifest:
        logger.info("No failures manifest at %s; nothing to retry.", pipeline_dir)
        return str(pipeline_dir)

    status_failed = bool(manifest.get("status_failed"))
    marketing_failed = list(manifest.get("marketing_failed") or [])

    if not status_failed and not marketing_failed:
        logger.info("Failures manifest empty at %s; nothing to retry.", pipeline_dir)
        return str(pipeline_dir)

    return generate_pipeline_report_from_draft(
        draft_path=draft_file,
        model=model,
        output_dir=pipeline_dir,
        pipelines_root=pipelines_root,
        only_slugs=marketing_failed,
        include_status=status_failed,
    )
