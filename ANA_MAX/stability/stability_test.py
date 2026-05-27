"""ANA MAX bridge stability test.

Runs repeated safe calls through ana-max-bridge and records success rate and
latency per tool. Reports are written to TEMP/ana-max-test-suite/<timestamp>.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from test_all_tools import DEFAULT_BRIDGE_URL, SKIP_REASONS, call_tool, fetch_tools, params_for  # noqa: E402

REPORT_ROOT = Path(os.environ.get("TEMP", ".")) / "ana-max-test-suite"


def report_dir(name: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = REPORT_ROOT / stamp / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_report(rows: list[dict[str, Any]], output_dir: Path) -> None:
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for row in rows:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1
    payload = {"suite": "stability", "counts": counts, "results": rows}
    (output_dir / "stability_report.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    lines = ["# ANA MAX Stability Report", "", f"PASS: {counts['PASS']}", f"WARN: {counts['WARN']}", f"FAIL: {counts['FAIL']}", "", "| Tool | Class | Success Rate | Avg | Min | Max | Failures |", "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for row in rows:
        lines.append(f"| {row['tool']} | {row['classification']} | {row['success_rate']} | {row['avg_seconds']} | {row['min_seconds']} | {row['max_seconds']} | {row['failures']} |")
    (output_dir / "stability_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="ANA MAX safe bridge stability test.")
    parser.add_argument("--bridge-url", default=DEFAULT_BRIDGE_URL)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--limit", type=int, default=0, help="Limit number of tools for quick verification.")
    parser.add_argument("--include-risky", action="store_true")
    args = parser.parse_args()
    bridge_url = args.bridge_url.rstrip("/")
    if not bridge_url.startswith("http://127.0.0.1:"):
        raise SystemExit("Refusing non-localhost bridge URL.")

    tools = sorted(fetch_tools(bridge_url, args.timeout), key=lambda item: item["name"])
    if args.limit:
        tools = tools[: args.limit]
    rows: list[dict[str, Any]] = []
    for tool in tools:
        name = str(tool.get("name", ""))
        if name in SKIP_REASONS and not args.include_risky:
            rows.append({"tool": name, "classification": "WARN", "success_rate": 0, "avg_seconds": 0, "min_seconds": 0, "max_seconds": 0, "failures": args.iterations, "detail": SKIP_REASONS[name]})
            print(f"WARN {name}: skipped")
            continue
        samples = []
        failures = 0
        details = []
        params = params_for(tool)
        for _ in range(args.iterations):
            row = call_tool(bridge_url, name, params, args.timeout)
            samples.append(float(row["elapsed_seconds"]))
            if row["classification"] == "FAIL":
                failures += 1
                details.append(row["detail"])
            time.sleep(0.05)
        success_rate = round((args.iterations - failures) / max(args.iterations, 1), 3)
        classification = "PASS" if failures == 0 else ("WARN" if success_rate >= 0.8 else "FAIL")
        rows.append({"tool": name, "classification": classification, "success_rate": success_rate, "avg_seconds": round(mean(samples), 3), "min_seconds": round(min(samples), 3), "max_seconds": round(max(samples), 3), "failures": failures, "detail": "; ".join(details[:3])})
        print(f"{classification} {name}: success_rate={success_rate}")
    out = report_dir("stability")
    write_report(rows, out)
    print(f"Report folder: {out}")
    return 1 if any(row["classification"] == "FAIL" for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
