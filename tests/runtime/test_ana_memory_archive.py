"""Tests for explicit ANA memory archive planning/apply safety."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_memory_archive.py"


def load_script():
    script_dir = str(SCRIPT.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("ana_memory_archive", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _seed_memory_files(root: Path, count: int = 3) -> None:
    docs = root / "docs"
    rem = docs / "rem_sleep"
    rem.mkdir(parents=True)
    for index in range(count):
        (docs / f"SESSION_CHECKPOINT_2026-05-31T000{index}00Z0000.md").write_text("checkpoint", encoding="utf-8")
        (rem / f"REM_SLEEP_REPORT_2026-05-31T000{index}00+0000.md").write_text("rem", encoding="utf-8")


def test_archive_plan_is_dry_run_by_default(monkeypatch, tmp_path: Path):
    archive = load_script()
    ana_root = tmp_path / "ANA_MAX"
    _seed_memory_files(ana_root)
    monkeypatch.setattr(archive, "ANA_ROOT", ana_root)
    monkeypatch.setattr(archive.ana_memory_hygiene, "ANA_ROOT", ana_root)
    monkeypatch.setattr(archive.ana_memory_hygiene, "ARCHIVE_DIR", ana_root / "dev_artifacts" / "archives")

    plan = archive.build_archive_plan(keep_latest=1)

    assert plan["mode"] == "dry_run"
    assert plan["total_moves"] == 4
    assert plan["archive_date_basis"] == "utc"
    assert plan["summary"]["by_kind"] == {"checkpoints": 2, "rem_sleep_reports": 2}
    assert plan["summary"]["bytes"] > 0
    assert plan["safety"]["default_dry_run"] is True
    assert plan["moves"][0]["sha256"]
    assert all((ana_root / move["source"]).exists() for move in plan["moves"])


def test_summarize_moves_counts_kind_bytes_and_conflicts():
    archive = load_script()

    summary = archive.summarize_moves([
        {"source": "docs/SESSION_CHECKPOINT_A.md", "bytes": 10, "source_exists": True, "target_exists": False},
        {"source": "docs/rem_sleep/REM_SLEEP_REPORT_A.md", "bytes": 5, "source_exists": False, "target_exists": True},
        {"source": "docs/OTHER.md", "bytes": 2, "source_exists": True, "target_exists": False},
    ])

    assert summary["by_kind"] == {"checkpoints": 1, "other": 1, "rem_sleep_reports": 1}
    assert summary["bytes"] == 17
    assert summary["missing_sources"] == 1
    assert summary["existing_targets"] == 1


def test_archive_apply_requires_confirm(monkeypatch, tmp_path: Path):
    archive = load_script()
    ana_root = tmp_path / "ANA_MAX"
    _seed_memory_files(ana_root)
    monkeypatch.setattr(archive, "ANA_ROOT", ana_root)
    monkeypatch.setattr(archive.ana_memory_hygiene, "ANA_ROOT", ana_root)
    monkeypatch.setattr(archive.ana_memory_hygiene, "ARCHIVE_DIR", ana_root / "dev_artifacts" / "archives")
    plan = archive.build_archive_plan(keep_latest=1)

    try:
        archive.apply_archive(plan, confirm="")
    except PermissionError as exc:
        assert "ARCHIVE_OLD_MEMORY" in str(exc)
    else:
        raise AssertionError("archive apply should require explicit confirmation")


def test_archive_apply_moves_only_confirmed_candidates(monkeypatch, tmp_path: Path):
    archive = load_script()
    ana_root = tmp_path / "ANA_MAX"
    _seed_memory_files(ana_root)
    monkeypatch.setattr(archive, "ANA_ROOT", ana_root)
    monkeypatch.setattr(archive.ana_memory_hygiene, "ANA_ROOT", ana_root)
    monkeypatch.setattr(archive.ana_memory_hygiene, "ARCHIVE_DIR", ana_root / "dev_artifacts" / "archives")
    plan = archive.build_archive_plan(keep_latest=1)

    result = archive.apply_archive(plan, confirm=archive.CONFIRM_PHRASE)

    assert result["mode"] == "applied"
    assert result["applied_count"] == 4
    assert result["skipped_count"] == 0
    for move in result["applied"]:
        assert not (ana_root / move["source"]).exists()
        assert (ana_root / move["target"]).exists()


def test_archive_verify_passes_after_confirmed_apply(monkeypatch, tmp_path: Path):
    archive = load_script()
    ana_root = tmp_path / "ANA_MAX"
    _seed_memory_files(ana_root)
    monkeypatch.setattr(archive, "ANA_ROOT", ana_root)
    monkeypatch.setattr(archive.ana_memory_hygiene, "ANA_ROOT", ana_root)
    monkeypatch.setattr(archive.ana_memory_hygiene, "ARCHIVE_DIR", ana_root / "dev_artifacts" / "archives")
    plan = archive.build_archive_plan(keep_latest=1)
    applied = archive.apply_archive(plan, confirm=archive.CONFIRM_PHRASE)

    verification = archive.verify_archive(applied)

    assert verification["status"] == "PASS"
    assert verification["verified_count"] == 4
    assert verification["failed_count"] == 0


def test_archive_verify_fails_when_target_hash_changes(monkeypatch, tmp_path: Path):
    archive = load_script()
    ana_root = tmp_path / "ANA_MAX"
    _seed_memory_files(ana_root)
    monkeypatch.setattr(archive, "ANA_ROOT", ana_root)
    monkeypatch.setattr(archive.ana_memory_hygiene, "ANA_ROOT", ana_root)
    monkeypatch.setattr(archive.ana_memory_hygiene, "ARCHIVE_DIR", ana_root / "dev_artifacts" / "archives")
    plan = archive.build_archive_plan(keep_latest=1)
    applied = archive.apply_archive(plan, confirm=archive.CONFIRM_PHRASE)
    first_target = ana_root / applied["applied"][0]["target"]
    first_target.write_text("tampered", encoding="utf-8")

    verification = archive.verify_archive(applied)

    assert verification["status"] == "FAIL"
    assert verification["failed_count"] == 1
    assert verification["failed"][0]["sha256_ok"] is False


def test_archive_readiness_passes_for_clean_dry_run_plan(monkeypatch, tmp_path: Path):
    archive = load_script()
    ana_root = tmp_path / "ANA_MAX"
    _seed_memory_files(ana_root)
    monkeypatch.setattr(archive, "ANA_ROOT", ana_root)
    monkeypatch.setattr(archive.ana_memory_hygiene, "ANA_ROOT", ana_root)
    monkeypatch.setattr(archive.ana_memory_hygiene, "ARCHIVE_DIR", ana_root / "dev_artifacts" / "archives")
    plan = archive.build_archive_plan(keep_latest=1)

    readiness = archive.check_archive_readiness(plan)

    assert readiness["status"] == "PASS"
    assert readiness["total_moves"] == 4
    assert readiness["archive_date_basis"] == "utc"
    assert readiness["failures"] == []
    assert "ARCHIVE_OLD_MEMORY" in readiness["apply_command"]


def test_archive_readiness_fails_for_existing_target(monkeypatch, tmp_path: Path):
    archive = load_script()
    ana_root = tmp_path / "ANA_MAX"
    _seed_memory_files(ana_root)
    monkeypatch.setattr(archive, "ANA_ROOT", ana_root)
    monkeypatch.setattr(archive.ana_memory_hygiene, "ANA_ROOT", ana_root)
    monkeypatch.setattr(archive.ana_memory_hygiene, "ARCHIVE_DIR", ana_root / "dev_artifacts" / "archives")
    plan = archive.build_archive_plan(keep_latest=1)
    plan["moves"][0]["target_exists"] = True

    readiness = archive.check_archive_readiness(plan)

    assert readiness["status"] == "FAIL"
    assert any(item.startswith("target_exists:") for item in readiness["failures"])
