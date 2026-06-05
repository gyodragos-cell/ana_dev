from __future__ import annotations

import json
import sys
from pathlib import Path


ANA_MAX_DIR = Path(__file__).resolve().parents[2] / "ANA_MAX"
if str(ANA_MAX_DIR) not in sys.path:
    sys.path.insert(0, str(ANA_MAX_DIR))

from core.event_stream import EventStream, EventType  # noqa: E402
from tools.session_audit_tool import SessionAuditTool  # noqa: E402
import tools.session_audit_tool as session_audit  # noqa: E402


def test_session_audit_generates_hash_chain_and_trust_score(tmp_path: Path, monkeypatch) -> None:
    stream = EventStream(db_path=str(tmp_path / "events.db"))
    stream.emit(
        EventType.TOOL_RESULT,
        "code_context_pack",
        {"tool": "code_context_pack", "args": {"task": "inspect"}, "status": "success", "code_map": True},
        success=True,
    )
    stream.emit(
        EventType.TOOL_RESULT,
        "error_radar",
        {"tool": "error_radar", "args": {}, "status": "success"},
        success=True,
    )
    stream.emit(
        EventType.TOOL_RESULT,
        "tool_healthcheck",
        {"tool": "tool_healthcheck", "args": {}, "status": "success"},
        success=True,
    )

    monkeypatch.setattr(session_audit, "get_event_stream", lambda: stream)
    monkeypatch.setattr(session_audit, "DEFAULT_AUDIT_DIR", tmp_path / "audit")
    monkeypatch.setattr(session_audit, "DEFAULT_REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(session_audit, "_identity_surface_summary", lambda: {
        "schema": "ana.session_identity_surface.v1",
        "available": True,
        "status": "PASS",
        "files_checked": 10,
        "violations": 0,
        "missing_required": 0,
    })

    result = SessionAuditTool().execute(action="generate", run_id="test-run", hours=1, limit=10)

    assert result.is_success
    assert result.data["schema"] == "ana.session_audit.v1"
    assert result.data["trust"]["score"] == 100
    assert result.data["identity_surface"]["status"] == "PASS"
    assert len(result.data["events"]) == 3
    assert result.data["events"][0]["integrity"]["prev_hash"] == "0" * 64
    assert result.data["integrity"]["chain_head"] == result.data["events"][-1]["integrity"]["chain_hash"]
    assert Path(result.data["file"]).exists()

    saved = json.loads(Path(result.data["file"]).read_text(encoding="utf-8"))
    assert saved["run_id"] == "test-run"
    assert saved["events"][0]["replay"]["result_hash"]


def test_session_audit_redacts_private_paths_and_secrets(tmp_path: Path, monkeypatch) -> None:
    stream = EventStream(db_path=str(tmp_path / "events.db"))
    stream.emit(
        EventType.TOOL_RESULT,
        "file_patch",
        {
            "tool": "file_patch",
            "args": {
                "path": r"C:\Users\billy\Desktop\ana_dev\ANA_MAX\secret.py",
                "api_key": "abc123",
            },
            "status": "success",
        },
        success=True,
    )
    monkeypatch.setattr(session_audit, "get_event_stream", lambda: stream)
    monkeypatch.setattr(session_audit, "DEFAULT_REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(session_audit, "_identity_surface_summary", lambda: {
        "schema": "ana.session_identity_surface.v1",
        "available": True,
        "status": "PASS",
        "files_checked": 10,
        "violations": 0,
        "missing_required": 0,
    })

    result = SessionAuditTool().execute(action="replay", run_id="redact-run", hours=1, limit=5)

    assert result.is_success
    payload = json.dumps(result.data)
    assert "abc123" not in payload
    assert "billy" not in payload


def test_session_audit_includes_compact_trace_summary(tmp_path: Path, monkeypatch) -> None:
    stream = EventStream(db_path=str(tmp_path / "events.db"))
    stream.emit(
        EventType.TOOL_RESULT,
        "tool_healthcheck",
        {"tool": "tool_healthcheck", "args": {}, "status": "success"},
        success=True,
    )
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    (report_dir / "trace_report_20260531_010000.json").write_text(
        json.dumps(
            {
                "schema": "ana.trace_report.v1",
                "ok": True,
                "run_id": "trace-run",
                "autonomy_status": "PASS",
                "trust_score": 100,
                "steps": 12,
                "spans": 12,
                "aligned": True,
                "operations": {"verification": 5},
                "span_errors": [],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(session_audit, "get_event_stream", lambda: stream)
    monkeypatch.setattr(session_audit, "DEFAULT_REPORT_DIR", report_dir)
    monkeypatch.setattr(session_audit, "_identity_surface_summary", lambda: {
        "schema": "ana.session_identity_surface.v1",
        "available": True,
        "status": "PASS",
        "files_checked": 10,
        "violations": 0,
        "missing_required": 0,
    })

    result = SessionAuditTool().execute(action="trust", run_id="trace-audit", hours=1, limit=5)

    assert result.is_success
    assert result.data["trace"]["schema"] == "ana.session_trace_summary.v1"
    assert result.data["trace"]["available"] is True
    assert result.data["trace"]["aligned"] is True
    assert result.data["trace"]["raw_private_payloads"] is False
    assert result.data["identity_surface"]["status"] == "PASS"


def test_session_audit_identity_failure_caps_trust_score(tmp_path: Path, monkeypatch) -> None:
    stream = EventStream(db_path=str(tmp_path / "events.db"))
    stream.emit(
        EventType.TOOL_RESULT,
        "code_context_pack",
        {"tool": "code_context_pack", "args": {"task": "inspect"}, "status": "success", "code_map": True},
        success=True,
    )
    stream.emit(
        EventType.TOOL_RESULT,
        "error_radar",
        {"tool": "error_radar", "args": {}, "status": "success"},
        success=True,
    )
    stream.emit(
        EventType.TOOL_RESULT,
        "tool_healthcheck",
        {"tool": "tool_healthcheck", "args": {}, "status": "success"},
        success=True,
    )

    monkeypatch.setattr(session_audit, "get_event_stream", lambda: stream)
    monkeypatch.setattr(session_audit, "DEFAULT_REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(session_audit, "_identity_surface_summary", lambda: {
        "schema": "ana.session_identity_surface.v1",
        "available": True,
        "status": "FAIL",
        "files_checked": 10,
        "violations": 1,
        "missing_required": 0,
    })

    result = SessionAuditTool().execute(action="trust", run_id="identity-cap", hours=1, limit=10)

    assert result.is_success
    assert result.data["trust"]["score"] == 70
    assert result.data["trust"]["signals"]["identity_cap_applied"] is True
    assert result.data["identity_surface"]["status"] == "FAIL"
