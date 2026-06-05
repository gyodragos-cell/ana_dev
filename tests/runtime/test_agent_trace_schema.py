from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANA_MAX_DIR = ROOT / "ANA_MAX"
if str(ANA_MAX_DIR) not in sys.path:
    sys.path.insert(0, str(ANA_MAX_DIR))

from core.agent_trace_schema import make_span, stable_digest, validate_span


def test_make_span_stores_digests_not_raw_payloads() -> None:
    span = make_span(
        run_id="run-1",
        operation="tool_call",
        status="ok",
        tool_name="web_fetch",
        input_payload={"url": "https://example.com", "api_key": "secret-value"},
        result_payload={"status": "success"},
        evidence={"path": r"C:\Users\billy\Desktop\ana_dev\file.txt"},
        started_at=100.0,
        ended_at=101.25,
    )

    assert span["schema"] == "ana.agent_trace_span.v1"
    assert span["trace_id"] == "run-1"
    assert span["tool_name"] == "web_fetch"
    assert span["duration_ms"] == 1250
    assert span["raw_private_payloads"] is False
    assert "secret-value" not in str(span)
    assert "billy" not in str(span)
    assert validate_span(span) == []


def test_stable_digest_redacts_sensitive_values() -> None:
    assert stable_digest({"token": "a"}) == stable_digest({"token": "b"})


def test_validate_span_reports_bad_shape() -> None:
    errors = validate_span({"schema": "wrong", "operation": "unknown"})

    assert "invalid:schema" in errors
    assert "invalid:operation" in errors
    assert "missing:run_id" in errors


def test_make_span_rejects_unknown_operation() -> None:
    try:
        make_span(run_id="run-1", operation="raw_memory_dump", status="ok")
    except ValueError as exc:
        assert "Unsupported trace operation" in str(exc)
    else:
        raise AssertionError("expected ValueError")
