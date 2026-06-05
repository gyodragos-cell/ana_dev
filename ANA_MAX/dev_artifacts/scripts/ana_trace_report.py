"""Summarize and validate local ANA trace spans from autonomy reports."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
REPORT_DIR = ANA_ROOT / "dev_artifacts" / "reports"

if str(ANA_ROOT) not in sys.path:
    sys.path.insert(0, str(ANA_ROOT))

from core.agent_trace_schema import validate_span


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def latest_autonomy_report(report_dir: Path = REPORT_DIR) -> Path | None:
    reports = sorted(report_dir.glob("autonomy_runner_*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    return reports[0] if reports else None


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def summarize_report(path: Path) -> dict[str, Any]:
    report = load_json(path)
    steps = report.get("steps") or []
    spans = report.get("trace_spans") or []
    span_errors = []
    for index, span in enumerate(spans, 1):
        errors = validate_span(span) if isinstance(span, dict) else ["invalid:not_object"]
        if errors:
            span_errors.append({"index": index, "errors": errors})
    operations = Counter(str(span.get("operation") or "") for span in spans if isinstance(span, dict))
    statuses = Counter(str(span.get("status") or "") for span in spans if isinstance(span, dict))
    aligned = len(steps) == len(spans)
    ok = bool(aligned and not span_errors and spans)
    return {
        "schema": "ana.trace_report.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_report": str(path),
        "run_id": report.get("run_id"),
        "trace_id": report.get("trace_id"),
        "autonomy_status": report.get("status"),
        "trust_score": (report.get("signals") or {}).get("trust_score"),
        "steps": len(steps),
        "spans": len(spans),
        "aligned": aligned,
        "operations": dict(sorted(operations.items())),
        "statuses": dict(sorted(statuses.items())),
        "span_errors": span_errors,
        "ok": ok,
        "next_step": (
            "Trace spans are aligned; use this report for audit/replay-lite context."
            if ok else
            "Regenerate Autonomy Runner report or inspect span validation errors."
        ),
    }


def write_report(report: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"trace_report_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate/summarize ANA trace spans from an autonomy report.")
    parser.add_argument("--report", default="", help="Autonomy report path. Defaults to latest autonomy_runner_*.json.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = Path(args.report).resolve() if args.report else latest_autonomy_report()
    if not source or not source.exists():
        print("ANA Trace Report: FAIL no autonomy report found")
        return 1
    report = summarize_report(source)
    out = None if args.no_write else write_report(report)
    if args.json:
        print(json.dumps({**report, "report": str(out) if out else None}, indent=2, ensure_ascii=False))
    else:
        status = "PASS" if report["ok"] else "WARN"
        print(
            f"ANA Trace Report: {status} "
            f"steps={report['steps']} spans={report['spans']} aligned={report['aligned']} "
            f"ops={report['operations']}"
        )
        print(f"next_action={report['next_step']}")
        if out:
            print(f"report={out}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
