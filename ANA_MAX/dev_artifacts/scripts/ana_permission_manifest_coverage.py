"""Check permission_manifest coverage against runtime-registered tools."""

from __future__ import annotations

import argparse
import contextlib
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
MANIFEST_PATH = ANA_ROOT / "config" / "permission_manifest.json"
REPORT_DIR = ANA_ROOT / "dev_artifacts" / "reports"


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_manifest_tools(path: Path = MANIFEST_PATH) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    tools = payload.get("tools", {})
    if not isinstance(tools, dict):
        return set()
    return set(tools)


def load_runtime_tools() -> set[str]:
    os.environ.setdefault("VSCODE_AGENT", "1")
    if str(ANA_ROOT) not in sys.path:
        sys.path.insert(0, str(ANA_ROOT))

    with contextlib.redirect_stdout(io.StringIO()):
        import main as ana_main  # type: ignore
        from tools.base import registry

        registry.reset()
        ana_main._register_all_tools()
        return set(registry.list_tools())


def compare_tool_sets(runtime_tools: set[str], manifest_tools: set[str]) -> dict[str, Any]:
    missing = sorted(runtime_tools - manifest_tools)
    extra = sorted(manifest_tools - runtime_tools)
    return {
        "schema": "ana.permission_manifest.coverage.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "PASS" if not missing and not extra else "FAIL",
        "runtime_tools": len(runtime_tools),
        "manifest_tools": len(manifest_tools),
        "missing_in_manifest": missing,
        "extra_in_manifest": extra,
    }


def write_report(report: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"permission_manifest_coverage_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def print_human(report: dict[str, Any], report_path: Path | None = None) -> None:
    print(
        "ANA Permission Manifest Coverage: "
        f"{report['status']} runtime={report['runtime_tools']} manifest={report['manifest_tools']} "
        f"missing={len(report['missing_in_manifest'])} extra={len(report['extra_in_manifest'])}"
    )
    if report["missing_in_manifest"]:
        print("missing_in_manifest=" + ", ".join(report["missing_in_manifest"]))
    if report["extra_in_manifest"]:
        print("extra_in_manifest=" + ", ".join(report["extra_in_manifest"]))
    if report_path:
        print(f"report={report_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check ANA permission manifest coverage.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = compare_tool_sets(load_runtime_tools(), load_manifest_tools())
    report_path = None if args.no_write else write_report(report)
    if args.json:
        print(json.dumps({**report, "report": str(report_path) if report_path else None}, indent=2, ensure_ascii=False))
    else:
        print_human(report, report_path)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
