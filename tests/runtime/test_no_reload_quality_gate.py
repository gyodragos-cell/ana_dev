"""Tests for the no-reload quality gate advisory behavior."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "no_reload_quality_gate.py"


def load_script():
    spec = importlib.util.spec_from_file_location("no_reload_quality_gate", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_run_advisory_maps_pass_to_ok(monkeypatch):
    gate = load_script()

    monkeypatch.setattr(
        gate,
        "run_step",
        lambda step: {
            "name": step.name,
            "status": "pass",
            "returncode": 0,
            "stdout_tail": "ANA Live Reload: PASS marker=True",
            "stderr_tail": "",
        },
    )

    result = gate.run_advisory(gate.Step("live_reload_marker", ["demo"], 10))

    assert result["status"] == "ok"
    assert result["returncode"] == 0


def test_run_advisory_maps_failure_to_warn(monkeypatch):
    gate = load_script()

    monkeypatch.setattr(
        gate,
        "run_step",
        lambda step: {
            "name": step.name,
            "status": "fail",
            "returncode": 1,
            "stdout_tail": "ANA Live Reload: WARN marker=False",
            "stderr_tail": "",
        },
    )

    result = gate.run_advisory(gate.Step("live_reload_marker", ["demo"], 10))

    assert result["status"] == "warn"
    assert result["returncode"] == 1
    assert "marker=False" in result["stdout_tail"]


def test_no_reload_gate_includes_local_checkpoint_tests():
    text = SCRIPT.read_text(encoding="utf-8")

    assert "ana_local_checkpoint.py" in text
    assert "ana_operator_status.py" in text
    assert "ana_lab_state_summary.py" in text
    assert "ana_post_reload_verify.py" in text
    assert "ana_file_activity_snapshot.py" in text
    assert "ana_live_tool_surface_check.py" in text
    assert "ana_live_behavior_check.py" in text
    assert "ana_identity_surface_check.py" in text
    assert "ana_vsix_version_check.py" in text
    assert "ana_nucleus_smoke.py" in text
    assert "test_ana_local_checkpoint.py" in text
    assert "test_ana_operator_status.py" in text
    assert "test_ana_lab_state_summary.py" in text
    assert "test_ana_post_reload_verify.py" in text
    assert "test_ana_file_activity_snapshot.py" in text
    assert "test_ana_live_tool_surface_check.py" in text
    assert "test_ana_live_behavior_check.py" in text
    assert "test_ana_identity_surface_check.py" in text
    assert "test_ana_vsix_version_check.py" in text
    assert "test_ana_nucleus_smoke.py" in text
    assert "test_session_checkpoint_tool.py" in text
    assert "vsix_version_consistency" in text
    assert "live_tool_surface" in text
    assert "live_behavior" in text
    assert "identity_surface_check" in text
