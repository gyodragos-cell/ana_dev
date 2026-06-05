"""Tests for session checkpoint latest-handoff behavior."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = ROOT / "ANA_MAX" / "tools" / "session_checkpoint_tool.py"


def load_tool_module():
    ana_root = str(ROOT / "ANA_MAX")
    if ana_root not in sys.path:
        sys.path.insert(0, ana_root)
    spec = importlib.util.spec_from_file_location("session_checkpoint_tool", TOOL_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_latest_pointer_preserves_manual_notes(tmp_path):
    module = load_tool_module()
    tool = module.SessionCheckpointTool()
    tool.docs_dir = tmp_path
    latest = tmp_path / "CURRENT_SESSION_HANDOFF.md"
    latest.write_text(
        "\n".join([
            "# Current Session Handoff",
            "",
            "Latest checkpoint: `old.md`",
            "Timestamp: old",
            "Memory topic: `old`",
            "",
            "Open the checkpoint file for the full handoff.",
            "",
            "## Standard Reload Flow",
            "",
            "Keep this operator note.",
            "",
        ]),
        encoding="utf-8",
    )

    tool._write_latest_pointer(
        tmp_path / "SESSION_CHECKPOINT_NEW.md",
        {
            "timestamp": "2026-05-31T01:20:00+00:00",
            "memory_topic": "session_checkpoint_new",
        },
    )

    text = latest.read_text(encoding="utf-8")

    assert "Latest checkpoint: `SESSION_CHECKPOINT_NEW.md`" in text
    assert "Memory topic: `session_checkpoint_new`" in text
    assert "## Standard Reload Flow" in text
    assert "Keep this operator note." in text


def test_latest_pointer_without_existing_notes_stays_compact(tmp_path):
    module = load_tool_module()
    tool = module.SessionCheckpointTool()
    tool.docs_dir = tmp_path

    tool._write_latest_pointer(
        tmp_path / "SESSION_CHECKPOINT_NEW.md",
        {
            "timestamp": "2026-05-31T01:20:00+00:00",
            "memory_topic": "session_checkpoint_new",
        },
    )

    text = (tmp_path / "CURRENT_SESSION_HANDOFF.md").read_text(encoding="utf-8")

    assert "Latest checkpoint: `SESSION_CHECKPOINT_NEW.md`" in text
    assert "Open the checkpoint file for the full handoff." in text
    assert "## Standard Reload Flow" not in text


def test_refresh_memory_archive_report_returns_compact_metadata(tmp_path, monkeypatch):
    module = load_tool_module()
    tool = module.SessionCheckpointTool()
    tool.root = tmp_path
    report_path = tmp_path / "memory_archive.json"

    fake_archive = SimpleNamespace(
        build_archive_plan=lambda: {
            "mode": "dry_run",
            "total_moves": 12,
            "archive_date_basis": "utc",
        },
        write_report=lambda plan: report_path,
    )
    monkeypatch.setitem(sys.modules, "ana_memory_archive", fake_archive)

    refresh = tool._refresh_memory_archive_report()

    assert refresh == {
        "mode": "dry_run",
        "total_moves": 12,
        "archive_date_basis": "utc",
        "report": str(report_path),
    }


def test_refresh_memory_archive_report_is_best_effort(tmp_path, monkeypatch):
    module = load_tool_module()
    tool = module.SessionCheckpointTool()
    tool.root = tmp_path

    fake_archive = SimpleNamespace(
        build_archive_plan=lambda: (_ for _ in ()).throw(RuntimeError("archive unavailable")),
    )
    monkeypatch.setitem(sys.modules, "ana_memory_archive", fake_archive)

    refresh = tool._refresh_memory_archive_report()

    assert refresh["status"] == "WARN"
    assert "archive unavailable" in refresh["error"]
