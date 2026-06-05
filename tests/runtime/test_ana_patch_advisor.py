from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_patch_advisor.py"


def load_script():
    script_dir = str(SCRIPT.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("ana_patch_advisor", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_patch_advisor_recommends_review_for_large_dirty_tree():
    advisor = load_script()
    recommendations = advisor.build_recommendations(
        [{"kind": "large_dirty_tree", "severity": "medium"}],
        [
            "ANA_MAX/docs/SESSION_CHECKPOINT_2026-05-31T000000Z0000.md",
            "docs/examples/EXAMPLE.md",
            "tests/runtime/test_example.py",
            "ANA_MAX/dev_artifacts/scripts/tool.py",
        ],
    )

    first = recommendations[0]
    assert first["apply_automatically"] is False
    assert "patch blindly" in first["title"]
    assert "operator approval" in first["next_step"]


def test_patch_advisor_uses_error_radar_dirty_tree_details():
    advisor = load_script()
    recommendations = advisor.build_recommendations(
        [
            {
                "kind": "large_dirty_tree",
                "severity": "medium",
                "details": {
                    "total": 352,
                    "tracked": 40,
                    "untracked": 312,
                    "checkpoints": 205,
                    "docs": 229,
                    "tests": 41,
                    "runtime": 0,
                },
            }
        ],
        ["ANA_MAX/dev_artifacts/scripts/tool.py"],
    )

    assert "352 changed paths" in recommendations[0]["evidence"]
    assert "205 checkpoints" in recommendations[0]["evidence"]
    assert "Error Radar" in recommendations[0]["evidence"]


def test_patch_advisor_prefers_local_dirty_tree_details():
    advisor = load_script()
    recommendations = advisor.build_recommendations(
        [
            {
                "kind": "large_dirty_tree",
                "severity": "medium",
                "details": {
                    "total": 352,
                    "tracked": 40,
                    "untracked": 312,
                    "checkpoints": 205,
                    "docs": 229,
                    "tests": 41,
                    "runtime": 0,
                },
            }
        ],
        ["ANA_MAX/dev_artifacts/scripts/tool.py"],
        dirty_tree={
            "schema": "ana.dirty_tree_report.v1",
            "total": 371,
            "tracked": 40,
            "untracked": 331,
            "categories": {
                "checkpoint": 184,
                "rem_sleep": 40,
                "doc": 31,
                "test": 41,
                "runtime": 23,
                "script": 42,
            },
        },
    )

    assert "371 changed paths" in recommendations[0]["evidence"]
    assert "184 checkpoints" in recommendations[0]["evidence"]
    assert "23 runtime" in recommendations[0]["evidence"]
    assert "local Dirty Tree" in recommendations[0]["evidence"]


def test_patch_advisor_adds_active_work_batch_recommendation():
    advisor = load_script()
    recommendations = advisor.build_recommendations(
        [{"kind": "large_dirty_tree", "severity": "medium"}],
        [],
        dirty_tree={
            "schema": "ana.dirty_tree_report.v1",
            "total": 145,
            "tracked": 20,
            "untracked": 125,
            "categories": {"runtime": 23, "script": 42, "test": 43},
            "active_work": {
                "review_batches": [
                    {
                        "category": "runtime",
                        "count": 23,
                        "tracked": 17,
                        "untracked": 6,
                        "sample": ["ANA_MAX/tools/error_radar_tool.py"],
                        "next_step": "Run focused runtime tests and inspect owning modules first.",
                        "suggested_commands": ["python -m compileall -q ANA_MAX/core ANA_MAX/tools"],
                    },
                    {
                        "category": "script",
                        "count": 42,
                        "tracked": 2,
                        "untracked": 40,
                        "sample": ["ANA_MAX/dev_artifacts/scripts/ana_dirty_tree_report.py"],
                        "next_step": "Run focused script tests or dry-run CLIs before relying on automation.",
                    },
                ]
            },
        },
    )

    batch = recommendations[1]
    assert batch["title"] == "Review active work batches before choosing a patch"
    assert batch["apply_automatically"] is False
    assert "runtime=23" in batch["evidence"]
    assert batch["suggested_files"] == ["ANA_MAX/tools/error_radar_tool.py"]
    assert batch["next_step"].startswith("Run focused runtime tests")


def test_patch_advisor_adds_blast_radius_recommendation():
    advisor = load_script()
    recommendations = advisor.build_recommendations(
        [],
        ["ANA_MAX/tools/tool_healthcheck.py"],
        {
            "available": True,
            "affected": [
                {
                    "name": "ANA_MAX/tools/tool_healthcheck.py",
                    "score": 100,
                    "confidence": "EXACT",
                    "low_signal": False,
                },
                {
                    "name": "ANA_MAX/docs/SESSION_CHECKPOINT_old.md",
                    "score": 38,
                    "confidence": "INFERRED",
                    "low_signal": True,
                },
            ],
        },
    )

    assert recommendations[0]["title"] == "Review graph blast-radius before editing"
    assert recommendations[0]["apply_automatically"] is False
    assert recommendations[0]["suggested_files"] == ["ANA_MAX/tools/tool_healthcheck.py"]


def test_patch_advisor_recommends_runtime_investigation_for_traceback():
    advisor = load_script()
    recommendations = advisor.build_recommendations(
        [{"kind": "traceback", "severity": "high"}],
        ["ANA_MAX/tools/error_radar_tool.py"],
    )

    assert recommendations[0]["apply_automatically"] is False
    assert "runtime finding" in recommendations[0]["title"]
    assert "regression test" in recommendations[0]["next_step"]


def test_patch_advisor_no_finding_stays_read_only():
    advisor = load_script()
    recommendations = advisor.build_recommendations([], [])

    assert recommendations[0]["apply_automatically"] is False
    assert recommendations[0]["title"] == "No patch candidate from current diagnostics"


def test_patch_advisor_filters_debugger_traceback_text_noise():
    advisor = load_script()
    findings = [
        {
            "kind": "traceback",
            "severity": "high",
            "summary": "INFO - HTTP /mcp tools/call start name=debugger args=['action', 'traceback_text']",
        },
        {"kind": "large_dirty_tree", "severity": "medium", "summary": "changed paths"},
    ]

    normalized = advisor.normalize_findings(findings)

    assert len(normalized) == 1
    assert normalized[0]["kind"] == "large_dirty_tree"


def test_build_report_is_suggest_only(monkeypatch):
    advisor = load_script()
    monkeypatch.setattr(advisor, "call_tool", lambda *args, **kwargs: {
        "success": True,
        "data": {"findings": []},
    })
    monkeypatch.setattr(advisor, "git_changed_paths", lambda: [])
    monkeypatch.setattr(advisor, "build_blast_radius", lambda paths: {
        "available": False,
        "candidates": [],
        "affected_count": 0,
    })
    monkeypatch.setattr(advisor.ana_dirty_tree_report, "build_report", lambda limit=12: {
        "schema": "ana.dirty_tree_report.v1",
        "total": 0,
        "tracked": 0,
        "untracked": 0,
        "categories": {},
    })

    report = advisor.build_report("http://127.0.0.1:8766/mcp")

    assert report["schema"] == "ana.patch_advisor.v1"
    assert report["mode"] == "suggest_only"
    assert report["policy"]["read_only"] is True
    assert report["policy"]["writes_files"] is False
    assert report["inputs"]["dirty_tree_available"] is True
    assert report["inputs"]["blast_radius_available"] is False


def test_build_report_tracks_noise_filtered(monkeypatch):
    advisor = load_script()
    monkeypatch.setattr(advisor, "call_tool", lambda *args, **kwargs: {
        "success": True,
        "data": {
            "findings": [
                {
                    "kind": "traceback",
                    "summary": "INFO - TOOL START name=debugger args={'traceback_text': 'ValueError'}",
                },
                {"kind": "large_dirty_tree", "summary": "changed paths"},
            ]
        },
    })
    monkeypatch.setattr(advisor, "git_changed_paths", lambda: [])
    monkeypatch.setattr(advisor, "build_blast_radius", lambda paths: {
        "available": False,
        "candidates": [],
        "affected_count": 0,
    })
    monkeypatch.setattr(advisor.ana_dirty_tree_report, "build_report", lambda limit=12: {
        "schema": "ana.dirty_tree_report.v1",
        "total": 2,
        "tracked": 1,
        "untracked": 1,
        "categories": {"doc": 1, "test": 1},
    })

    report = advisor.build_report("http://127.0.0.1:8766/mcp")

    assert report["inputs"]["raw_finding_count"] == 2
    assert report["inputs"]["finding_count"] == 1
    assert report["inputs"]["noise_filtered"] == 1


def test_build_report_includes_blast_radius(monkeypatch):
    advisor = load_script()
    monkeypatch.setattr(advisor, "call_tool", lambda *args, **kwargs: {
        "success": True,
        "data": {"findings": []},
    })
    monkeypatch.setattr(advisor, "git_changed_paths", lambda: ["ANA_MAX/tools/tool_healthcheck.py"])
    monkeypatch.setattr(advisor, "build_blast_radius", lambda paths: {
        "available": True,
        "candidates": paths,
        "affected_count": 1,
        "affected": [
            {
                "name": "ANA_MAX/tools/tool_healthcheck.py",
                "score": 100,
                "confidence": "EXACT",
                "low_signal": False,
            }
        ],
    })
    monkeypatch.setattr(advisor.ana_dirty_tree_report, "build_report", lambda limit=12: {
        "schema": "ana.dirty_tree_report.v1",
        "total": 1,
        "tracked": 1,
        "untracked": 0,
        "categories": {"runtime": 1},
        "active_work": {
            "review_batches": [
                {
                    "category": "runtime",
                    "count": 1,
                    "tracked": 1,
                    "untracked": 0,
                        "sample": ["ANA_MAX/tools/tool_healthcheck.py"],
                        "next_step": "Run focused runtime tests and inspect owning modules first.",
                        "suggested_commands": ["python -m compileall -q ANA_MAX/core ANA_MAX/tools"],
                    }
                ]
            },
    })

    report = advisor.build_report("http://127.0.0.1:8766/mcp")

    assert report["inputs"]["blast_radius_available"] is True
    assert report["inputs"]["blast_radius_candidates"] == 1
    assert report["inputs"]["blast_radius_affected"] == 1
    assert report["blast_radius"]["affected"][0]["name"] == "ANA_MAX/tools/tool_healthcheck.py"
    assert report["dirty_tree"]["review_batches"][0]["category"] == "runtime"
    assert report["dirty_tree"]["review_batches"][0]["suggested_commands"]
