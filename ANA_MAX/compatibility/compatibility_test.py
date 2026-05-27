"""ANA MAX bridge compatibility tester for params vs legacy input payloads."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from test_all_tools import DEFAULT_BRIDGE_URL, SKIP_REASONS, classify_response, fetch_tools, params_for  # noqa: E402

REPORT_ROOT = Path(os.environ.get("TEMP", ".")) / "ana-max-test-suite"


def post_payload(bridge_url: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        response = requests.post(f"{bridge_url}/tools/call", json=payload, timeout=timeout)
        elapsed = round(time.perf_counter() - started, 3)
        try:
            body: Any = response.json()
        except ValueError:
            body = {"raw": response.text[:1000]}
        cls, detail = classify_response(response.status_code, body)
        return {"classification": cls, "http_status": response.status_code, "elapsed_seconds": elapsed, "detail": detail, "body": body}
    except requests.RequestException as exc:
        return {"classification": "FAIL", "http_status": "EXCEPTION", "elapsed_seconds": round(time.perf_counter() - started, 3), "detail": str(exc), "body": {}}


def output_dir() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = REPORT_ROOT / stamp / "compatibility"
    path.mkdir(parents=True, exist_ok=True)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="ANA MAX bridge compatibility matrix.")
    parser.add_argument("--bridge-url", default=DEFAULT_BRIDGE_URL)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--limit", type=int, default=0)
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
            rows.append({"tool": name, "classification": "WARN", "params_status": "SKIP", "input_status": "SKIP", "detail": SKIP_REASONS[name]})
            print(f"WARN {name}: skipped")
            continue
        params = params_for(tool)
        params_result = post_payload(bridge_url, {"tool": name, "params": params}, args.timeout)
        input_result = post_payload(bridge_url, {"tool": name, "input": params}, args.timeout)
        legacy_accepted = input_result["classification"] == "PASS"
        classification = "PASS" if params_result["classification"] != "FAIL" and not legacy_accepted else "WARN"
        if params_result["classification"] == "FAIL":
            classification = "FAIL"
        detail = "legacy input accepted" if legacy_accepted else params_result["detail"]
        rows.append({"tool": name, "classification": classification, "params_status": params_result["classification"], "input_status": input_result["classification"], "params_http": params_result["http_status"], "input_http": input_result["http_status"], "detail": detail})
        print(f"{classification} {name}: params={params_result['classification']} input={input_result['classification']}")
    counts = {key: sum(1 for row in rows if row["classification"] == key) for key in ("PASS", "WARN", "FAIL")}
    out = output_dir()
    (out / "compatibility_test.json").write_text(json.dumps({"suite": "compatibility", "counts": counts, "results": rows}, indent=2, default=str), encoding="utf-8")
    lines = ["# ANA MAX Compatibility Matrix", "", f"PASS: {counts['PASS']}", f"WARN: {counts['WARN']}", f"FAIL: {counts['FAIL']}", "", "| Tool | Class | Params | Input | Detail |", "| --- | --- | --- | --- | --- |"]
    for row in rows:
        lines.append(f"| {row['tool']} | {row['classification']} | {row['params_status']} | {row['input_status']} | {str(row['detail']).replace('|', '/')} |")
    (out / "compatibility_test.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report folder: {out}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
