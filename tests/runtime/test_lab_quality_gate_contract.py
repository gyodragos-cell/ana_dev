"""Tests for lab quality gate coverage contract."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "lab_quality_gate.py"


def test_lab_quality_gate_includes_local_checkpoint_contract():
    text = SCRIPT.read_text(encoding="utf-8")

    assert "ana_local_checkpoint.py" in text
    assert "ana_operator_status.py" in text
    assert "ana_lab_state_summary.py" in text
    assert "ana_post_reload_verify.py" in text
    assert "ana_trace_report.py" in text
    assert "ana_file_activity_snapshot.py" in text
    assert "ana_live_behavior_check.py" in text
    assert "ana_identity_surface_check.py" in text
    assert "ana_vsix_version_check.py" in text
    assert "test_ana_local_checkpoint.py" in text
    assert "test_ana_operator_status.py" in text
    assert "test_ana_lab_state_summary.py" in text
    assert "test_ana_post_reload_verify.py" in text
    assert "test_ana_trace_report.py" in text
    assert "test_ana_file_activity_snapshot.py" in text
    assert "test_ana_live_behavior_check.py" in text
    assert "test_ana_identity_surface_check.py" in text
    assert "test_ana_vsix_version_check.py" in text
    assert "test_ana_nucleus_smoke.py" in text
    assert "test_session_checkpoint_tool.py" in text
    assert "identity_surface_check" in text
    assert "trace_report" in text
    assert "vsix_version_consistency" in text
