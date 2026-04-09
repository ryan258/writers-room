"""
Helpers for naming and locating generated session artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re


DEFAULT_TRANSCRIPTS_DIR = Path("transcripts")
DEFAULT_FINAL_DIR = Path("final")
DEFAULT_PIPELINES_DIR = Path("pipelines")


@dataclass(frozen=True)
class ArtifactPaths:
    date_stamp: str
    title_slug: str
    transcript_path: Path
    brief_path: Path
    final_draft_path: Path
    pipeline_dir: Path


def slugify_filename(
    value: str,
    fallback: str = "untitled",
    *,
    max_words: int = 6,
    max_chars: int = 48,
) -> str:
    """Return a filesystem-safe slug capped for readable artifact names."""
    words = re.findall(r"[a-z0-9]+", value.lower())
    if max_words > 0:
        words = words[:max_words]

    selected: list[str] = []
    for word in words:
        candidate = "-".join([*selected, word])
        if max_chars > 0 and len(candidate) > max_chars:
            if not selected:
                return word[:max_chars].strip("-") or fallback
            break
        selected.append(word)

    slug = "-".join(selected).strip("-")
    return slug or fallback


def extract_markdown_title(markdown: str) -> str | None:
    """Return the first Markdown heading, if present."""
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line.startswith("#"):
            continue
        title = line.lstrip("#").strip()
        if title:
            return title
    return None


def build_artifact_paths(
    *,
    title: str,
    transcript_dir: str | Path = DEFAULT_TRANSCRIPTS_DIR,
    final_dir: str | Path = DEFAULT_FINAL_DIR,
    pipeline_dir: str | Path = DEFAULT_PIPELINES_DIR,
    now: datetime | None = None,
) -> ArtifactPaths:
    """Build the canonical output paths for a session."""
    current = now or datetime.now()
    date_stamp = current.strftime("%y%m%d")
    title_slug = slugify_filename(title)
    transcript_root = Path(transcript_dir)
    final_root = Path(final_dir)
    pipeline_root = Path(pipeline_dir)

    base_name = f"{date_stamp}_{title_slug}"
    return ArtifactPaths(
        date_stamp=date_stamp,
        title_slug=title_slug,
        transcript_path=transcript_root / f"{base_name}_transcript.txt",
        brief_path=transcript_root / f"{base_name}_brief.html",
        final_draft_path=final_root / f"{base_name}_final.md",
        pipeline_dir=pipeline_root / base_name,
    )


def derive_title_slug_from_final_path(path: str | Path) -> str:
    """Recover the stable title slug from ``YYMMDD_title_final.md``."""
    stem = derive_pipeline_dirname_from_final_path(path)
    match = re.match(r"^\d{6}_(.+)$", stem)
    if match:
        return match.group(1)
    return slugify_filename(stem)


def derive_pipeline_dirname_from_final_path(path: str | Path) -> str:
    """Recover the canonical pipeline directory name from a final draft path."""
    stem = re.sub(r"_final$", "", Path(path).stem)
    match = re.match(r"^(\d{6})_(.+)$", stem)
    if match:
        return f"{match.group(1)}_{slugify_filename(match.group(2))}"
    return slugify_filename(stem)
