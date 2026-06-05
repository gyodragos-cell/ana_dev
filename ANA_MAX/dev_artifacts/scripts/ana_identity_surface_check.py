"""Check active ANA lab identity surface for Codex-first neutrality.

This intentionally scans only active identity files, not historical reports,
archives, checkpoints, or sandbox material. Retired-tool mentions are allowed
only when they are clearly framed as retired/historical.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
REPORT_DIR = ANA_ROOT / "dev_artifacts" / "reports"

ACTIVE_FILES = [
    "AGENTS.md",
    "docs/ANA_LAB_MASTER_CONTEXT.md",
    "docs/CODEX_LAB_MANAGER_PROMPT.md",
    "docs/ANA_SERIOUS_PROJECT_RULES.md",
    "docs/LAB_README.md",
    "docs/DOCS_INDEX.md",
    "vscode_extension/package.json",
    "vscode_extension/README.md",
    "vscode_extension/CHANGELOG.md",
    "vscode_extension/MARKETPLACE.md",
]

REQUIRED_PHRASES = [
    "Codex",
    "ANA MAX",
]

FORBIDDEN_PATTERNS = [
    (re.compile(r"\bcodex\s+vs\b", re.IGNORECASE), "comparative_codex_vs"),
    (re.compile(r"\bvs\s+adal\b", re.IGNORECASE), "comparative_vs_adal"),
    (re.compile(r"\bqoder\b", re.IGNORECASE), "external_tool_qoder"),
    (re.compile(r"\bantigravity\b", re.IGNORECASE), "external_tool_antigravity"),
    (re.compile(r"\bwindsurf\b", re.IGNORECASE), "external_tool_windsurf"),
    (re.compile(r"\badal\b", re.IGNORECASE), "external_tool_adal"),
]

ALLOWED_CONTEXT_WORDS = {
    "external_tool_adal": {"retired", "historical", "removed", "not active"},
}


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def line_allowed(rule: str, line: str) -> bool:
    allowed = ALLOWED_CONTEXT_WORDS.get(rule)
    if not allowed:
        return False
    lowered = line.lower()
    return any(word in lowered for word in allowed)


def scan_file(path: Path, rel: str) -> list[dict[str, Any]]:
    if not path.exists():
        return [{"file": rel, "line": 0, "rule": "missing_file", "text": ""}]
    violations = []
    for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        for pattern, rule in FORBIDDEN_PATTERNS:
            if pattern.search(line) and not line_allowed(rule, line):
                violations.append({
                    "file": rel,
                    "line": number,
                    "rule": rule,
                    "text": line.strip()[:240],
                })
    return violations


def build_report(files: list[str] | None = None) -> dict[str, Any]:
    files = files or ACTIVE_FILES
    violations: list[dict[str, Any]] = []
    required_presence = {phrase: False for phrase in REQUIRED_PHRASES}
    for rel in files:
        path = REPO_ROOT / rel
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace")
            for phrase in REQUIRED_PHRASES:
                if phrase in text:
                    required_presence[phrase] = True
        violations.extend(scan_file(path, rel))
    missing_required = [phrase for phrase, present in required_presence.items() if not present]
    return {
        "schema": "ana.identity_surface_check.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "PASS" if not violations and not missing_required else "FAIL",
        "files_checked": len(files),
        "required_presence": required_presence,
        "missing_required": missing_required,
        "violations": violations,
        "policy": {
            "identity": "Codex-first / ANA-for-Codex",
            "external_tools": "neutral research input only; no active promotion",
            "retired_tools": "may be mentioned only as retired/historical",
        },
    }


def write_report(report: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"identity_surface_check_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check active Codex-first identity surface.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report()
    path = None if args.no_write else write_report(report)
    if args.json:
        print(json.dumps({**report, "report": str(path) if path else None}, indent=2, ensure_ascii=False))
    else:
        print(
            "ANA Identity Surface: "
            f"{report['status']} files={report['files_checked']} "
            f"violations={len(report['violations'])} "
            f"missing_required={len(report['missing_required'])}"
        )
        for item in report["violations"][:12]:
            print(f"[VIOLATION] {item['file']}:{item['line']} {item['rule']}: {item['text']}")
        if path:
            print(f"report={path}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
