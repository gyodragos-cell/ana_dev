"""Tests for ANA dirty tree classifier."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_dirty_tree_report.py"


def load_script():
    spec = importlib.util.spec_from_file_location("ana_dirty_tree_report", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_classify_dirty_tree_paths():
    script = load_script()

    assert script.classify("ANA_MAX/docs/SESSION_CHECKPOINT_2026.md") == "checkpoint"
    assert script.classify("ANA_MAX/docs/CURRENT_SESSION_HANDOFF.md") == "checkpoint"
    assert script.classify("ANA_MAX/docs/rem_sleep/REM_SLEEP_REPORT.md") == "rem_sleep"
    assert script.classify("ANA_MAX/dev_artifacts/reports/gate.json") == "report"
    assert script.classify("ANA_MAX/tools/tool_router_tool.py") == "runtime"
    assert script.classify("ANA_MAX/dev_artifacts/scripts/ana_dirty_tree_report.py") == "script"
    assert script.classify("tests/runtime/test_demo.py") == "test"
    assert script.classify("vscode_extension/extension.js") == "extension"
    assert script.classify("docs/DOCS_INDEX.md") == "doc"


def test_build_report_groups_active_and_generated(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "git_status_lines", lambda: [
        " M ANA_MAX/tools/tool_router_tool.py",
        "?? ANA_MAX/docs/SESSION_CHECKPOINT_2026.md",
        " M ANA_MAX/docs/CURRENT_SESSION_HANDOFF.md",
        "?? ANA_MAX/docs/rem_sleep/REM_SLEEP_REPORT.md",
        "?? tests/runtime/test_ana_dirty_tree_report.py",
        " M vscode_extension/extension.js",
    ])

    report = script.build_report(limit=4)

    assert report["schema"] == "ana.dirty_tree_report.v1"
    assert report["total"] == 6
    assert report["tracked"] == 3
    assert report["untracked"] == 3
    assert report["categories"]["runtime"] == 1
    assert report["categories"]["checkpoint"] == 2
    assert report["active_work"]["count"] == 3
    assert report["active_work"]["categories"] == {"extension": 1, "runtime": 1, "test": 1}
    assert report["active_work"]["by_category"]["runtime"]["count"] == 1
    assert report["active_work"]["by_category"]["runtime"]["tracked"] == 1
    assert report["active_work"]["by_category"]["runtime"]["sample"] == ["ANA_MAX/tools/tool_router_tool.py"]
    assert report["active_work"]["by_category"]["test"]["untracked"] == 1
    assert [batch["category"] for batch in report["active_work"]["review_batches"]] == [
        "runtime",
        "test",
        "extension",
    ]
    assert report["active_work"]["review_batches"][0]["next_step"].startswith("Run focused runtime tests")
    assert report["active_work"]["review_batches"][0]["suggested_commands"][0].startswith("python -m compileall")
    assert "test_error_radar_tool.py" in report["active_work"]["review_batches"][0]["suggested_commands"][1]
    assert report["generated_or_memory"]["count"] == 3
    assert report["generated_or_memory"]["categories"] == {"checkpoint": 2, "rem_sleep": 1}
    assert report["generated_or_memory"]["by_category"]["checkpoint"]["sample"] == [
        "ANA_MAX/docs/SESSION_CHECKPOINT_2026.md",
        "ANA_MAX/docs/CURRENT_SESSION_HANDOFF.md",
    ]
    assert "real work" in report["active_work"]["next_step"]
    assert "explicit operator confirmation" in report["generated_or_memory"]["next_step"]
    assert "Read-only" in report["safety"]


def test_recommendation_warns_for_checkpoint_noise():
    script = load_script()
    recommendation = script.build_recommendation({"checkpoint": 51}, 60)

    assert recommendation.startswith("Do not commit blindly")
