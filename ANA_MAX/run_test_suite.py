"""ANA MAX full local test-suite runner.

Runs the standalone safe test modules from the ANA_DEV mother workspace. The
smoke tester remains in test_all_tools.py so other modules can import its helper
functions without recursion.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent

DEFAULT_TESTS = [
    ("Smoke Test", BASE / "test_all_tools.py", []),
    ("Stability Test", BASE / "stability" / "stability_test.py", []),
    ("Performance Benchmark", BASE / "benchmarks" / "perf_benchmark.py", []),
    ("Visual Test", BASE / "visual" / "visual_test.py", []),
    ("Compatibility Test", BASE / "compatibility" / "compatibility_test.py", []),
    ("Health Dashboard", BASE / "dashboard" / "health_dashboard.py", []),
    ("Security Test", BASE / "security" / "security_test.py", []),
]

QUICK_ARGS = {
    "Stability Test": ["--limit", "3", "--iterations", "1"],
    "Performance Benchmark": ["--limit", "3", "--runs", "1"],
    "Compatibility Test": ["--limit", "3"],
}


def run_test(name: str, path: Path, extra_args: list[str], timeout: int) -> str:
    print("\n==============================")
    print(f"RUNNING: {name}")
    print("==============================")
    if not path.exists():
        print(f"[SKIP] Missing: {path}")
        return "WARN"
    try:
        result = subprocess.run(
            [sys.executable, "-B", str(path), *extra_args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] {name} exceeded {timeout} seconds")
        return "FAIL"
    except Exception as exc:  # pragma: no cover - defensive runner guard
        print(f"[ERROR] {name}: {exc}")
        return "FAIL"
    if result.stdout:
        print(result.stdout)
    if result.stderr.strip():
        print("STDERR:", result.stderr)
    if result.returncode == 0:
        return "PASS"
    print(f"[FAIL] {name} exited with code {result.returncode}")
    return "FAIL"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ANA MAX local test-suite scripts.")
    parser.add_argument("--quick", action="store_true", help="Run shorter stability/benchmark/compatibility checks.")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    print("======================================")
    print(" ANA MAX - FULL TEST SUITE EXECUTION")
    print("======================================")
    print("Timestamp:", _dt.datetime.now(_dt.timezone.utc).isoformat())
    print("Reports root:", Path(os.environ.get("TEMP", ".")) / "ana-max-test-suite")

    statuses: list[tuple[str, str]] = []
    for name, path, base_args in DEFAULT_TESTS:
        extra_args = list(base_args)
        if args.quick:
            extra_args.extend(QUICK_ARGS.get(name, []))
        statuses.append((name, run_test(name, path, extra_args, args.timeout)))

    print("\n======================================")
    print(" SUMMARY")
    print("======================================")
    for name, status in statuses:
        print(f"{status:4} {name}")
    failed = sum(1 for _, status in statuses if status == "FAIL")
    print("Reports saved in %TEMP%/ana-max-test-suite/<timestamp>/")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
