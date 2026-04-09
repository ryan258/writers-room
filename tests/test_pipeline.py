import json
import threading
from datetime import datetime
from pathlib import Path

import pytest

from lib.artifacts import (
    build_artifact_paths,
    derive_pipeline_dirname_from_final_path,
    derive_title_slug_from_final_path,
    extract_markdown_title,
    slugify_filename,
)
import lib.pipeline as pipeline_module


# ---------------------------------------------------------------------------
# Artifact path helpers
# ---------------------------------------------------------------------------


def test_artifact_paths_use_short_date_and_title_slug(tmp_path):
    paths = build_artifact_paths(
        title="The Locked Closet",
        transcript_dir=tmp_path / "transcripts",
        final_dir=tmp_path / "final",
        pipeline_dir=tmp_path / "pipelines",
        now=datetime(2026, 4, 9, 12, 0, 0),
    )

    assert paths.transcript_path.name == "260409_the-locked-closet_transcript.txt"
    assert paths.brief_path.name == "260409_the-locked-closet_brief.html"
    assert paths.final_draft_path.name == "260409_the-locked-closet_final.md"
    assert paths.pipeline_dir.name == "260409_the-locked-closet"
    assert paths.pipeline_dir.parent == tmp_path / "pipelines"


def test_markdown_title_helpers_prefer_heading():
    markdown = "# The Closet\n\nIt hummed all night."

    assert extract_markdown_title(markdown) == "The Closet"
    assert (
        derive_pipeline_dirname_from_final_path("260409_the-closet_final.md")
        == "260409_the-closet"
    )
    assert derive_title_slug_from_final_path("260409_the-closet_final.md") == "the-closet"
    assert derive_title_slug_from_final_path("weird-name.md") == "weird-name"


def test_slugify_filename_caps_long_prompts():
    slug = slugify_filename(
        "A locked closet hums at night and something answers back from the dark hallway"
    )

    assert slug == "a-locked-closet-hums-at-night"


# ---------------------------------------------------------------------------
# Status call
# ---------------------------------------------------------------------------


def _status_json_payload() -> str:
    return json.dumps(
        {
            "editing_steps": [
                {
                    "step": "Intake two-pass draft",
                    "status": "complete",
                    "summary": "The source draft is cleanly formed.",
                    "next_action": "Move into the structural read.",
                }
            ],
            "polish_checklist": [
                {
                    "item": "Consistent POV",
                    "status": "pass",
                    "note": "The narration holds steady.",
                }
            ],
        }
    )


def test_generate_status_data_rejects_empty_draft():
    with pytest.raises(ValueError, match="empty draft"):
        pipeline_module.generate_status_data(draft_markdown="   ")


def test_render_status_markdown_renders_statuses_and_next_actions():
    report = pipeline_module.render_status_markdown(
        title="The Closet",
        draft_path="final/260409_the-closet_final.md",
        status_data={
            "editing_steps": [
                {
                    "step": "Intake two-pass draft",
                    "status": "complete",
                    "summary": "Ready.",
                    "next_action": "Move on.",
                },
                {
                    "step": "Structural read",
                    "status": "revise",
                    "summary": "Needs a cleaner midpoint.",
                    "next_action": "",
                },
            ],
            "polish_checklist": [
                {"item": "Consistent POV", "status": "pass", "note": "Steady."},
                {"item": "Tense check", "status": "revise", "note": "One slip."},
            ],
        },
    )

    assert "# The Closet — Status" in report
    assert "- [x] Intake two-pass draft (COMPLETE): Ready." in report
    assert "  Next: Move on." in report
    assert "- [ ] Structural read (REVISE): Needs a cleaner midpoint." in report
    assert "- [x] Consistent POV (PASS): Steady." in report
    assert "- [ ] Tense check (REVISE): One slip." in report


# ---------------------------------------------------------------------------
# Full pipeline run with fake Agent
# ---------------------------------------------------------------------------


class _CallLog:
    def __init__(self):
        self.lock = threading.Lock()
        self.active = 0
        self.peak = 0
        self.calls: list[str] = []

    def record(self, name: str) -> None:
        with self.lock:
            self.active += 1
            self.peak = max(self.peak, self.active)
            self.calls.append(name)

    def release(self) -> None:
        with self.lock:
            self.active -= 1


def _install_fake_agent(monkeypatch, *, fail_slugs: set[str] | None = None):
    """Replace pipeline_module.Agent with a deterministic fake."""
    fail_slugs = fail_slugs or set()
    log = _CallLog()

    class FakeAgent:
        def __init__(self, *, name, **kwargs):
            self.name = name
            self.kwargs = kwargs

        def generate_response(self, context, story_context=None):
            log.record(self.name)
            try:
                if self.name == "Pipeline Editor":
                    return _status_json_payload()
                # Marketing agent: name is "Marketing/<display>"
                if self.name.startswith("Marketing/"):
                    for slug, spec in pipeline_module._SPEC_BY_SLUG.items():
                        if self.name == f"Marketing/{spec.name}":
                            if slug in fail_slugs:
                                raise RuntimeError(f"boom {slug}")
                            return f"{spec.name} copy for draft."
                    raise AssertionError(f"Unknown marketing agent: {self.name}")
                raise AssertionError(f"Unexpected agent name: {self.name}")
            finally:
                log.release()

    monkeypatch.setattr(pipeline_module, "Agent", FakeAgent)
    return log


def _write_draft(tmp_path: Path) -> Path:
    draft_dir = tmp_path / "final"
    draft_dir.mkdir(parents=True, exist_ok=True)
    draft_path = draft_dir / "260409_the-closet_final.md"
    draft_path.write_text("# The Closet\n\nIt hummed all night.", encoding="utf-8")
    return draft_path


def test_generate_pipeline_report_writes_directory_with_all_assets(monkeypatch, tmp_path):
    draft_path = _write_draft(tmp_path)
    log = _install_fake_agent(monkeypatch)

    pipeline_dir_str = pipeline_module.generate_pipeline_report_from_draft(
        draft_path=draft_path,
        model="demo-model",
        pipelines_root=tmp_path / "pipelines",
    )

    pipeline_dir = Path(pipeline_dir_str)
    assert pipeline_dir == tmp_path / "pipelines" / "260409_the-closet"
    assert pipeline_dir.is_dir()

    # Status file
    status_md = (pipeline_dir / "status.md").read_text(encoding="utf-8")
    assert "# The Closet — Status" in status_md
    assert "Intake two-pass draft" in status_md

    # All eight marketing asset files
    marketing_dir = pipeline_dir / "marketing"
    expected_files = {
        spec.filename for spec in pipeline_module.MARKETING_ASSET_SPECS
    }
    assert {p.name for p in marketing_dir.iterdir()} == expected_files
    logline_md = (marketing_dir / "logline.md").read_text(encoding="utf-8")
    assert "# Logline" in logline_md
    assert "Logline copy for draft." in logline_md

    # Index links everything and reports no failures
    index_md = (pipeline_dir / "index.md").read_text(encoding="utf-8")
    assert "# The Closet — Pipeline" in index_md
    assert "[status.md](status.md)" in index_md
    assert "[Logline](marketing/logline.md)" in index_md
    assert "PENDING" not in index_md

    # No failures manifest written on a clean run
    assert not (pipeline_dir / pipeline_module.FAILURES_MANIFEST_NAME).exists()

    # Status + 8 marketing calls
    assert sum(1 for c in log.calls if c == "Pipeline Editor") == 1
    marketing_calls = [c for c in log.calls if c.startswith("Marketing/")]
    assert len(marketing_calls) == 8

    # Concurrent marketing calls are capped at the batch size.
    # Status runs first (outside the pool), so peak reflects marketing batch cap.
    assert log.peak <= pipeline_module.MARKETING_BATCH_SIZE


def test_pipeline_partial_failure_writes_manifest_and_marks_index(monkeypatch, tmp_path):
    draft_path = _write_draft(tmp_path)
    _install_fake_agent(monkeypatch, fail_slugs={"pull-quotes", "landing-page"})

    pipeline_dir = Path(
        pipeline_module.generate_pipeline_report_from_draft(
            draft_path=draft_path,
            model="demo-model",
            pipelines_root=tmp_path / "pipelines",
        )
    )

    # Successful assets still on disk
    assert (pipeline_dir / "marketing" / "logline.md").exists()
    assert not (pipeline_dir / "marketing" / "pull-quotes.md").exists()
    assert not (pipeline_dir / "marketing" / "landing-page.md").exists()

    # Index reflects pending items
    index_md = (pipeline_dir / "index.md").read_text(encoding="utf-8")
    assert "[Logline](marketing/logline.md)" in index_md
    assert "Pull quotes — PENDING" in index_md
    assert "Launch landing page — PENDING" in index_md

    # Failures manifest captures the two slugs
    manifest_path = pipeline_dir / pipeline_module.FAILURES_MANIFEST_NAME
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status_failed"] is False
    assert sorted(manifest["marketing_failed"]) == ["landing-page", "pull-quotes"]


def test_retry_regenerates_only_failed_items(monkeypatch, tmp_path):
    draft_path = _write_draft(tmp_path)

    # First run fails two assets
    _install_fake_agent(monkeypatch, fail_slugs={"pull-quotes", "landing-page"})
    pipeline_dir = Path(
        pipeline_module.generate_pipeline_report_from_draft(
            draft_path=draft_path,
            model="demo-model",
            pipelines_root=tmp_path / "pipelines",
        )
    )

    # Capture which assets had already landed so we can verify they aren't rewritten
    logline_path = pipeline_dir / "marketing" / "logline.md"
    logline_before = logline_path.read_text(encoding="utf-8")

    # Second run: retry with a healthy agent should only regenerate the two failures
    retry_log = _install_fake_agent(monkeypatch)
    retry_dir = Path(
        pipeline_module.retry_failed_pipeline_items(
            draft_path=draft_path,
            model="demo-model",
            pipelines_root=tmp_path / "pipelines",
        )
    )

    assert retry_dir == pipeline_dir
    marketing_calls = [c for c in retry_log.calls if c.startswith("Marketing/")]
    # Only the two previously-failed slugs should have been called
    assert sorted(marketing_calls) == sorted(
        [
            f"Marketing/{pipeline_module._SPEC_BY_SLUG['pull-quotes'].name}",
            f"Marketing/{pipeline_module._SPEC_BY_SLUG['landing-page'].name}",
        ]
    )
    # Status call should NOT have run on retry (status_failed was False)
    assert "Pipeline Editor" not in retry_log.calls

    # The previously successful logline file is untouched
    assert logline_path.read_text(encoding="utf-8") == logline_before

    # Failed files now exist
    assert (pipeline_dir / "marketing" / "pull-quotes.md").exists()
    assert (pipeline_dir / "marketing" / "landing-page.md").exists()

    # Manifest is removed when the retry resolves all failures
    assert not (pipeline_dir / pipeline_module.FAILURES_MANIFEST_NAME).exists()

    # Index no longer reports pending items
    index_md = (pipeline_dir / "index.md").read_text(encoding="utf-8")
    assert "PENDING" not in index_md


def test_retry_is_noop_when_manifest_missing(monkeypatch, tmp_path):
    draft_path = _write_draft(tmp_path)
    pipelines_root = tmp_path / "pipelines"

    log = _install_fake_agent(monkeypatch)
    retry_dir = pipeline_module.retry_failed_pipeline_items(
        draft_path=draft_path,
        model="demo-model",
        pipelines_root=pipelines_root,
    )

    # Should return the would-be directory, but with no work done
    assert retry_dir == str(pipelines_root / "260409_the-closet")
    assert log.calls == []


def test_generate_pipeline_report_scopes_directory_to_dated_final_path(monkeypatch, tmp_path):
    _install_fake_agent(monkeypatch)
    pipelines_root = tmp_path / "pipelines"

    first_draft = tmp_path / "final" / "260409_the-closet_final.md"
    first_draft.parent.mkdir(parents=True, exist_ok=True)
    first_draft.write_text("# The Closet\n\nNight one.", encoding="utf-8")

    second_draft = tmp_path / "final" / "260410_the-closet_final.md"
    second_draft.write_text("# The Closet\n\nNight two.", encoding="utf-8")

    first_dir = Path(
        pipeline_module.generate_pipeline_report_from_draft(
            draft_path=first_draft,
            model="demo-model",
            pipelines_root=pipelines_root,
        )
    )
    second_dir = Path(
        pipeline_module.generate_pipeline_report_from_draft(
            draft_path=second_draft,
            model="demo-model",
            pipelines_root=pipelines_root,
        )
    )

    assert first_dir == pipelines_root / "260409_the-closet"
    assert second_dir == pipelines_root / "260410_the-closet"
    assert first_dir != second_dir


def test_generate_marketing_asset_rejects_empty_draft():
    with pytest.raises(ValueError, match="empty draft"):
        pipeline_module.generate_marketing_asset(
            spec=pipeline_module.MARKETING_ASSET_SPECS[0],
            draft_markdown="   ",
        )
