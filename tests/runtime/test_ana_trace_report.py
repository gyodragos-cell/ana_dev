from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "ANA_MAX" / "dev_artifacts" / "scripts" / "ana_trace_report.py"
ANA_MAX_DIR = ROOT / "ANA_MAX"
if str(ANA_MAX_DIR) not in sys.path:
    sys.path.insert(0, str(ANA_MAX_DIR))

from core.agent_trace_schema import make_span


def load_script():
    spec = importlib.util.spec_from_file_location("ana_trace_report", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_trace_report_validates_aligned_autonomy_report(tmp_path: Path) -> None:
    trace_report = load_script()
    span = make_span(
        run_id="run-1",
        trace_id="run-1",
        operation="verification",
        tool_name="health",
        status="ok",
    )
    source = tmp_path / "autonomy_runner_test.json"
    source.write_text(
        trace_report.json.dumps({
            "run_id": "run-1",
            "trace_id": "run-1",
            "status": "PASS",
            "signals": {"trust_score": 95},
            "steps": [{"name": "health", "status": "PASS"}],
            "trace_spans": [span],
        }),
        encoding="utf-8",
    )

    report = trace_report.summarize_report(source)

    assert report["schema"] == "ana.trace_report.v1"
    assert report["ok"] is True
    assert report["aligned"] is True
    assert report["steps"] == 1
    assert report["spans"] == 1
    assert report["operations"] == {"verification": 1}
    assert report["span_errors"] == []


def test_trace_report_flags_missing_spans(tmp_path: Path) -> None:
    trace_report = load_script()
    source = tmp_path / "autonomy_runner_bad.json"
    source.write_text(
        trace_report.json.dumps({
            "status": "PASS",
            "steps": [{"name": "health", "status": "PASS"}],
            "trace_spans": [],
        }),
        encoding="utf-8",
    )

    report = trace_report.summarize_report(source)

    assert report["ok"] is False
    assert report["aligned"] is False
    assert "Regenerate" in report["next_step"]
