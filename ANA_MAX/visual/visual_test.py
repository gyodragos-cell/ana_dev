"""ANA MAX visual tool safe tester.

By default this script does not capture the screen. Pass --include-visual to run
read-only visual tools and save response previews in the report folder.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from test_all_tools import DEFAULT_BRIDGE_URL, call_tool, fetch_tools  # noqa: E402

REPORT_ROOT = Path(os.environ.get("TEMP", ".")) / "ana-max-test-suite"
VISUAL_PARAMS: dict[str, dict[str, Any]] = {
    "desktop_capture": {"format": "png", "save": False},
    "vision_region_capture": {"x": 0, "y": 0, "width": 320, "height": 200, "save": False},
    "vision_find_element": {"query": "Start", "confidence": 0.7, "dry_run": True},
    "uia_click": {"window_title": "__ana_max_safe_no_match__", "element_title": "__ana_max_safe_no_match__", "confirm": False},
}


def output_dir() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = REPORT_ROOT / stamp / "visual"
    path.mkdir(parents=True, exist_ok=True)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="ANA MAX safe visual bridge tester.")
    parser.add_argument("--bridge-url", default=DEFAULT_BRIDGE_URL)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--include-visual", action="store_true", help="Allow read-only screen capture tests.")
    args = parser.parse_args()
    bridge_url = args.bridge_url.rstrip("/")
    if not bridge_url.startswith("http://127.0.0.1:"):
        raise SystemExit("Refusing non-localhost bridge URL.")
    available = {str(tool.get("name")): tool for tool in fetch_tools(bridge_url, args.timeout)}
    rows: list[dict[str, Any]] = []
    for name, params in VISUAL_PARAMS.items():
        if name not in available:
            rows.append({"tool": name, "classification": "WARN", "detail": "tool not listed", "http_status": "MISSING", "elapsed_seconds": 0})
            print(f"WARN {name}: missing")
            continue
        if not args.include_visual and name != "uia_click":
            rows.append({"tool": name, "classification": "WARN", "detail": "screen capture skipped; rerun with --include-visual", "http_status": "SKIP", "elapsed_seconds": 0})
            print(f"WARN {name}: skipped visual capture")
            continue
        result = call_tool(bridge_url, name, dict(params), args.timeout)
        if name == "uia_click" and result["classification"] == "FAIL" and "not found" in str(result["detail"]).lower():
            result["classification"] = "WARN"
        rows.append(result)
        print(f"{result['classification']} {name}: {result['detail']}")
    counts = {key: sum(1 for row in rows if row["classification"] == key) for key in ("PASS", "WARN", "FAIL")}
    out = output_dir()
    (out / "visual_test.json").write_text(json.dumps({"suite": "visual", "counts": counts, "results": rows}, indent=2, default=str), encoding="utf-8")
    lines = ["# ANA MAX Visual Test", "", f"PASS: {counts['PASS']}", f"WARN: {counts['WARN']}", f"FAIL: {counts['FAIL']}", "", "| Tool | Class | HTTP | Seconds | Detail |", "| --- | --- | --- | ---: | --- |"]
    for row in rows:
        lines.append(f"| {row['tool']} | {row['classification']} | {row.get('http_status')} | {row.get('elapsed_seconds')} | {str(row.get('detail', '')).replace('|', '/')} |")
    (out / "visual_test.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report folder: {out}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
