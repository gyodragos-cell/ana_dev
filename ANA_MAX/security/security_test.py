"""ANA MAX safe security checks for bridge boundary and destructive tool policy."""
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
from test_all_tools import DEFAULT_BRIDGE_URL, SKIP_REASONS, classify_response, fetch_tools  # noqa: E402

REPORT_ROOT = Path(os.environ.get("TEMP", ".")) / "ana-max-test-suite"
DESTRUCTIVE_TOOLS = sorted({"edit", "file_patch", "desktop_control", "desktop_control_tool", "uia_click", "uia_type", "system_optimization"})


def output_dir() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = REPORT_ROOT / stamp / "security"
    path.mkdir(parents=True, exist_ok=True)
    return path


def post(bridge_url: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
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


def main() -> int:
    parser = argparse.ArgumentParser(description="ANA MAX safe security tester.")
    parser.add_argument("--bridge-url", default=DEFAULT_BRIDGE_URL)
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args()
    bridge_url = args.bridge_url.rstrip("/")
    if not bridge_url.startswith("http://127.0.0.1:"):
        raise SystemExit("Refusing non-localhost bridge URL.")
    tools = {str(tool.get("name")): tool for tool in fetch_tools(bridge_url, args.timeout)}
    rows: list[dict[str, Any]] = []

    invalid = post(bridge_url, {"tool": "__missing_tool__", "params": {}}, args.timeout)
    invalid_ok = invalid["classification"] != "PASS"
    rows.append({"check": "invalid_tool_rejected", "classification": "PASS" if invalid_ok else "FAIL", "detail": invalid["detail"], "http_status": invalid["http_status"]})

    malformed = post(bridge_url, {"params": {}}, args.timeout)
    malformed_ok = malformed["classification"] != "PASS"
    rows.append({"check": "malformed_call_rejected", "classification": "PASS" if malformed_ok else "FAIL", "detail": malformed["detail"], "http_status": malformed["http_status"]})

    for name in DESTRUCTIVE_TOOLS:
        if name not in tools:
            rows.append({"check": f"{name}_present", "classification": "WARN", "detail": "tool not listed", "http_status": "MISSING"})
            continue
        rows.append({"check": f"{name}_safe_policy", "classification": "PASS" if name in SKIP_REASONS else "FAIL", "detail": SKIP_REASONS.get(name, "missing safe skip policy"), "http_status": "POLICY"})

    payload_test = post(bridge_url, {"tool": "privacy_shield", "params": {"operation": "scan", "text": "token=not-a-real-secret test@example.com"}}, args.timeout) if "privacy_shield" in tools else {"classification": "WARN", "detail": "privacy_shield not listed", "http_status": "MISSING"}
    rows.append({"check": "privacy_payload_scan", "classification": payload_test["classification"], "detail": payload_test["detail"], "http_status": payload_test["http_status"]})

    counts = {key: sum(1 for row in rows if row["classification"] == key) for key in ("PASS", "WARN", "FAIL")}
    out = output_dir()
    (out / "security_test.json").write_text(json.dumps({"suite": "security", "counts": counts, "results": rows}, indent=2, default=str), encoding="utf-8")
    lines = ["# ANA MAX Security Test", "", f"PASS: {counts['PASS']}", f"WARN: {counts['WARN']}", f"FAIL: {counts['FAIL']}", "", "| Check | Class | HTTP | Detail |", "| --- | --- | --- | --- |"]
    for row in rows:
        lines.append(f"| {row['check']} | {row['classification']} | {row['http_status']} | {str(row['detail']).replace('|', '/')} |")
    (out / "security_test.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"PASS: {counts['PASS']} WARN: {counts['WARN']} FAIL: {counts['FAIL']}")
    print(f"Report folder: {out}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
