"""Tests for privacy-preserving file activity snapshots."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_file_activity_snapshot.py"


def load_script():
    spec = importlib.util.spec_from_file_location("ana_file_activity_snapshot", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_file_activity_snapshot_detects_created_deleted_and_modified(tmp_path: Path) -> None:
    script = load_script()
    root = tmp_path / "project"
    root.mkdir()
    keep = root / "keep.py"
    deleted = root / "old.txt"
    keep.write_text("one", encoding="utf-8")
    deleted.write_text("remove", encoding="utf-8")

    first_report, first_baseline = script.build_report(root)
    assert first_report["baseline_available"] is False

    deleted.unlink()
    keep.write_text("two plus metadata-visible change", encoding="utf-8")
    (root / "new.md").write_text("new", encoding="utf-8")
    second_manifest = script.scan_root(root)
    diff = script.diff_manifests(first_baseline["manifest"], second_manifest)

    assert diff["created"] == 1
    assert diff["deleted"] == 1
    assert diff["modified"] == 1
    assert diff["samples"]["deleted"][0]["path"] == "old.txt"


def test_file_activity_snapshot_skips_noise_and_does_not_read_content(tmp_path: Path) -> None:
    script = load_script()
    root = tmp_path / "project"
    (root / ".git").mkdir(parents=True)
    (root / "ANA_MAX" / "data").mkdir(parents=True)
    (root / "ANA_MAX" / "logs").mkdir(parents=True)
    (root / "src").mkdir(parents=True)
    (root / ".git" / "ignored").write_text("secret", encoding="utf-8")
    (root / "ANA_MAX" / "data" / "events_stream.db").write_text("volatile", encoding="utf-8")
    (root / "ANA_MAX" / "logs" / "ignored.log").write_text("secret", encoding="utf-8")
    (root / "src" / "app.py").write_text("print('ok')", encoding="utf-8")

    report, baseline = script.build_report(root)

    assert report["privacy"]["content_read"] is False
    assert report["privacy"]["raw_private_payloads"] is False
    assert list(baseline["manifest"]) == ["src/app.py"]
