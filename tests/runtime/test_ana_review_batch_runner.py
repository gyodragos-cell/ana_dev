"""Tests for ANA review batch runner."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_review_batch_runner.py"


def load_script():
    script_dir = str(SCRIPT.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("ana_review_batch_runner", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fake_batches():
    return [
        {
            "category": "runtime",
            "count": 2,
            "tracked": 1,
            "untracked": 1,
            "sample": ["ANA_MAX/tools/tool_router_tool.py"],
            "next_step": "Run focused runtime tests.",
            "suggested_commands": [
                "python -m compileall -q ANA_MAX/core ANA_MAX/tools",
                "python -m pytest tests/runtime/test_tool_router_tool.py -q",
            ],
        },
        {
            "category": "doc",
            "count": 1,
            "tracked": 1,
            "untracked": 0,
            "sample": ["docs/AGENT_MEMORY.md"],
            "next_step": "Check docs.",
            "suggested_commands": ["python ANA_MAX/dev_artifacts/scripts/ana_governance_check.py"],
        },
    ]


def test_build_report_defaults_to_first_batch_dry_run(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "active_review_batches", lambda limit=12: fake_batches())

    report = script.build_report()

    assert report["schema"] == "ana.review_batch_runner.v1"
    assert report["status"] == "DRY_RUN"
    assert report["mode"] == "dry_run"
    assert report["category"] == "runtime"
    assert report["commands"][0]["status"] == "planned"
    assert report["commands"][0]["argv"][0] == sys.executable
    assert report["policy"]["shell"] is False


def test_build_report_can_select_category_and_all_commands(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "active_review_batches", lambda limit=12: fake_batches())

    report = script.build_report(category="runtime", all_commands=True)

    assert len(report["commands"]) == 2
    assert report["available_batches"] == ["runtime", "doc"]


def test_build_report_all_batches_is_plan_only(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "active_review_batches", lambda limit=12: fake_batches())

    report = script.build_report(all_batches=True)

    assert report["status"] == "DRY_RUN"
    assert report["category"] == "all"
    assert report["policy"]["all_batches_plan_only"] is True
    assert [item["category"] for item in report["commands"]] == ["runtime", "runtime", "doc"]


def test_build_report_rejects_all_batches_execution(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "active_review_batches", lambda limit=12: fake_batches())

    try:
        script.build_report(all_batches=True, execute=True)
    except RuntimeError as exc:
        assert "plan-only" in str(exc)
    else:
        raise AssertionError("Expected all-batches execution rejection")


def test_run_mode_executes_selected_command(monkeypatch):
    script = load_script()
    monkeypatch.setattr(script, "active_review_batches", lambda limit=12: fake_batches())

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(script.subprocess, "run", fake_run)

    report = script.build_report(category="doc", execute=True)

    assert report["status"] == "PASS"
    assert report["commands"][0]["status"] == "pass"
    assert report["commands"][0]["stdout_tail"] == "ok"


def test_write_report_uses_unique_mode_and_category_filename(monkeypatch, tmp_path):
    script = load_script()
    monkeypatch.setattr(script, "REPORT_DIR", tmp_path)

    runtime = script.write_report({"mode": "run", "category": "runtime", "commands": []})
    doc = script.write_report({"mode": "run", "category": "doc", "commands": []})

    assert runtime != doc
    assert runtime.name.startswith("review_batch_runner_")
    assert runtime.name.endswith("_run_runtime.json")
    assert doc.name.endswith("_run_doc.json")
    assert runtime.exists()
    assert doc.exists()


def test_rejects_shell_metacharacters():
    script = load_script()

    try:
        script.command_to_argv("python -m pytest; Remove-Item important")
    except RuntimeError as exc:
        assert "shell metacharacters" in str(exc)
    else:
        raise AssertionError("Expected shell metacharacter rejection")


def test_rejects_non_python_command():
    script = load_script()

    try:
        script.command_to_argv("cmd /c dir")
    except RuntimeError as exc:
        assert "Only Python review commands" in str(exc)
    else:
        raise AssertionError("Expected non-Python command rejection")
