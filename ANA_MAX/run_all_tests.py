"""Run the full ANA MAX local test suite.

Standalone runner for ANA_DEV. It keeps going when a test fails, is missing, or
hits the timeout, and leaves each child test responsible for writing its own
reports under TEMP.
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
TIMEOUT_SECONDS = 120

TESTS = [
    ("test_all_tools.py", BASE / "test_all_tools.py"),
    ("stability/stability_test.py", BASE / "stability" / "stability_test.py"),
    ("benchmarks/perf_benchmark.py", BASE / "benchmarks" / "perf_benchmark.py"),
    ("visual/visual_test.py", BASE / "visual" / "visual_test.py"),
    ("compatibility/compatibility_test.py", BASE / "compatibility" / "compatibility_test.py"),
    ("dashboard/health_dashboard.py", BASE / "dashboard" / "health_dashboard.py"),
    ("security/security_test.py", BASE / "security" / "security_test.py"),
]


def run_one(label: str, path: Path) -> str:
    print("\n" + "=" * 72)
    print(f"RUNNING: {label}")
    print("=" * 72)

    if not path.exists():
        print(f"SKIP: missing test file: {path}")
        return "SKIP"

    try:
        result = subprocess.run(
            [sys.executable, "-B", str(path)],
            cwd=str(BASE),
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT: {label} exceeded {TIMEOUT_SECONDS} seconds")
        return "TIMEOUT"
    except Exception as exc:
        print(f"ERROR: {label}: {exc}")
        return "ERROR"

    if result.returncode == 0:
        print(f"PASS: {label}")
        return "PASS"

    print(f"ERROR: {label} exited with code {result.returncode}")
    return "ERROR"


def main() -> int:
    print("ANA MAX FULL TEST SUITE")
    print("Started:", datetime.now(timezone.utc).isoformat())
    print("Workspace:", BASE)
    print("Reports root:", Path(os.environ.get("TEMP", ".")) / "ana-max-test-suite")

    results = []
    for label, path in TESTS:
        results.append((label, run_one(label, path)))

    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    for label, status in results:
        print(f"{status:7} {label}")

    print("ALL TESTS COMPLETED — reports saved in %TEMP%/ana-max-test-suite/<timestamp>/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
