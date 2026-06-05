"""Tests for ANA memory hygiene report."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_memory_hygiene.py"


def load_script():
    spec = importlib.util.spec_from_file_location("ana_memory_hygiene", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_summarize_files_counts_archive_candidates(tmp_path: Path):
    script = load_script()
    files = []
    for index in range(5):
        path = tmp_path / f"SESSION_CHECKPOINT_2026-05-31T000{index}00Z0000.md"
        path.write_text("checkpoint", encoding="utf-8")
        files.append(path)

    summary = script._summarize_files(files, keep_latest=2)

    assert summary["count"] == 5
    assert summary["keep_latest"] == 2
    assert summary["archive_candidates"] == 3
    assert len(summary["latest"]) == 2


def test_default_keep_latest_policy_is_twenty():
    script = load_script()

    assert script.DEFAULT_KEEP_LATEST == 20


def test_build_report_is_read_only_shape(monkeypatch, tmp_path: Path):
    script = load_script()
    ana_root = tmp_path / "ANA_MAX"
    docs = ana_root / "docs"
    rem = docs / "rem_sleep"
    rem.mkdir(parents=True)
    (docs / "SESSION_CHECKPOINT_2026-05-31T000000Z0000.md").write_text("one", encoding="utf-8")
    (rem / "REM_SLEEP_REPORT_2026-05-31T000000+0000.md").write_text("two", encoding="utf-8")
    monkeypatch.setattr(script, "ANA_ROOT", ana_root)

    report = script.build_report(keep_latest=1)

    assert report["schema"] == "ana.memory_hygiene.v1"
    assert report["mode"] == "report_only"
    assert report["checkpoints"]["count"] == 1
    assert report["rem_sleep_reports"]["count"] == 1
    assert "No files were moved" in report["safety"]


def test_build_report_can_include_dry_run_archive_plan(monkeypatch, tmp_path: Path):
    script = load_script()
    ana_root = tmp_path / "ANA_MAX"
    docs = ana_root / "docs"
    rem = docs / "rem_sleep"
    rem.mkdir(parents=True)
    for index in range(3):
        (docs / f"SESSION_CHECKPOINT_2026-05-31T000{index}00Z0000.md").write_text("checkpoint", encoding="utf-8")
        (rem / f"REM_SLEEP_REPORT_2026-05-31T000{index}00+0000.md").write_text("rem", encoding="utf-8")
    monkeypatch.setattr(script, "ANA_ROOT", ana_root)
    monkeypatch.setattr(script, "ARCHIVE_DIR", ana_root / "dev_artifacts" / "archives")

    report = script.build_report(keep_latest=1, include_plan=True)

    assert report["mode"] == "archive_plan"
    assert report["archive_plan"]["total_moves"] == 4
    assert report["archive_plan"]["archive_date_basis"] == "utc"
    assert report["archive_plan"]["apply_supported"] is False
    assert report["archive_plan"]["checkpoints"][0]["source"].startswith("docs/SESSION_CHECKPOINT_")
    assert report["archive_plan"]["checkpoints"][0]["target"].startswith("dev_artifacts/archives/memory_hygiene_")
    assert report["archive_plan"]["rem_sleep_reports"][0]["source"].startswith("docs/rem_sleep/REM_SLEEP_REPORT_")
