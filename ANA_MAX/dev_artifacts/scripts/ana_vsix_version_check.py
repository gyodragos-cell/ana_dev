"""Check that active lab VSIX docs point to the package.json version."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_JSON = REPO_ROOT / "vscode_extension" / "package.json"
CHECK_FILES = [
    "vscode_extension/README.md",
    "vscode_extension/MARKETPLACE.md",
    "docs/ANA_OPERATOR_RELOAD_RUNBOOK.md",
    "docs/examples/LAB_VSIX_INSTALL_HELPER_EXAMPLE.md",
    "docs/examples/OPERATOR_STATUS_EXAMPLE.md",
    "ANA_MAX/docs/CURRENT_SESSION_HANDOFF.md",
]


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def package_version() -> str:
    package = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    return str(package.get("version") or "")


def find_versions(text: str) -> list[str]:
    return sorted(set(re.findall(r"1\.0\.\d+", text)))


def build_report() -> dict[str, Any]:
    expected = package_version()
    files = []
    mismatches = []
    for relative in CHECK_FILES:
        path = REPO_ROOT / relative
        if not path.exists():
            files.append({"path": relative, "exists": False, "versions": [], "status": "missing"})
            mismatches.append(relative)
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        versions = find_versions(text)
        stale = [version for version in versions if version != expected]
        status = "PASS" if not stale else "FAIL"
        files.append({"path": relative, "exists": True, "versions": versions, "stale": stale, "status": status})
        if stale:
            mismatches.append(relative)
    return {
        "schema": "ana.vsix_version_check.v1",
        "expected_version": expected,
        "status": "PASS" if not mismatches else "FAIL",
        "mismatches": mismatches,
        "files": files,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check active VSIX version references.")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(
            "ANA VSIX Version: "
            f"{report['status']} expected={report['expected_version']} "
            f"mismatches={len(report['mismatches'])}"
        )
        for item in report["files"]:
            print(f"[{item['status']}] {item['path']} versions={','.join(item.get('versions') or []) or 'none'}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
