"""Check how ready ANA MAX Lab is for a future Linux/Mate mirror.

The checker is intentionally static and conservative. It does not try to make
Windows code disappear; it labels what can move as core/shared and what should
stay behind a Windows profile.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import re
import sys
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = REPO_ROOT / "ANA_MAX" / "dev_artifacts" / "reports"

TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".json",
    ".md",
    ".toml",
    ".yaml",
    ".yml",
    ".ps1",
    ".bat",
    ".cmd",
    ".txt",
}

IGNORE_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "memory",
    "logs",
    "screenshots",
    "archives",
    "vsix_build_1.0.41",
    "vsix_verify_1.0.41",
}

PATTERNS = [
    ("windows_path", re.compile(r"[A-Za-z]:\\|C:/"), "hard-coded Windows path"),
    ("powershell", re.compile(r"\bpowershell(?:\.exe)?\b|PowerShell", re.I), "PowerShell dependency"),
    ("cmd_shell", re.compile(r"\bcmd(?:\.exe)?\b|\.bat\b|\.cmd\b", re.I), "Windows CMD/BAT dependency"),
    ("win32_api", re.compile(r"\bwin32|pywin32|win32gui|win32api|win32con\b", re.I), "Win32/pywin32 dependency"),
    ("uia", re.compile(r"\bUIAutomation|uia|windows_uia\b", re.I), "Windows UI Automation dependency"),
    ("sapi", re.compile(r"\bSAPI|System\.Speech|pyttsx3\b", re.I), "Windows voice/TTS dependency"),
    ("registry", re.compile(r"\bregistry\b|HKCU:|HKLM:", re.I), "Windows registry dependency"),
]

LINUX_POSITIVE = [
    ("pathlib", re.compile(r"from pathlib import Path|\bPath\("), "uses pathlib"),
    ("posix_hint", re.compile(r"\bbash\b|\bLinux\b|\bapt install\b", re.I), "mentions Linux/POSIX path"),
]


@dataclass(frozen=True)
class Finding:
    kind: str
    path: str
    line: int
    detail: str
    text: str

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "path": self.path,
            "line": self.line,
            "detail": self.detail,
            "text": self.text[:220],
        }


def should_skip(path: Path) -> bool:
    rel_parts = set(path.relative_to(REPO_ROOT).parts)
    return bool(rel_parts & IGNORE_PARTS)


def iter_text_files(paths: Iterable[Path]) -> Iterable[Path]:
    for root in paths:
        root = root if root.is_absolute() else REPO_ROOT / root
        if not root.exists():
            continue
        if root.is_file():
            if root.suffix.lower() in TEXT_EXTENSIONS and not should_skip(root):
                yield root
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS and not should_skip(path):
                yield path


def scan_file(path: Path) -> tuple[list[Finding], list[Finding]]:
    findings: list[Finding] = []
    positives: list[Finding] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return findings, positives

    rel = path.relative_to(REPO_ROOT).as_posix()
    for index, line in enumerate(lines, start=1):
        for kind, pattern, detail in PATTERNS:
            if pattern.search(line):
                findings.append(Finding(kind, rel, index, detail, line.strip()))
        for kind, pattern, detail in LINUX_POSITIVE:
            if pattern.search(line):
                positives.append(Finding(kind, rel, index, detail, line.strip()))
    return findings, positives


def classify_path(path: str) -> str:
    lower = path.lower()
    if any(token in lower for token in ["windows", "uia", "desktop", "input_probe", "voice", "tts"]):
        return "windows_profile"
    if lower.endswith(".ps1") or lower.endswith(".bat") or lower.endswith(".cmd"):
        return "windows_profile"
    if "/docs/" in f"/{lower}" or lower.startswith("docs/"):
        return "docs"
    if lower.startswith("vscode_extension/"):
        return "extension"
    if lower.startswith("tests/"):
        return "tests"
    return "core_candidate"


def summarize(findings: list[Finding], positives: list[Finding]) -> dict[str, object]:
    by_kind: dict[str, int] = {}
    by_profile: dict[str, int] = {}
    affected_files: set[str] = set()
    for finding in findings:
        by_kind[finding.kind] = by_kind.get(finding.kind, 0) + 1
        profile = classify_path(finding.path)
        by_profile[profile] = by_profile.get(profile, 0) + 1
        affected_files.add(finding.path)

    positive_files = {item.path for item in positives if item.kind == "pathlib"}
    blocker_kinds = {"windows_path", "win32_api", "powershell", "cmd_shell", "registry"}
    core_blocker_files = {
        item.path
        for item in findings
        if classify_path(item.path) == "core_candidate" and item.kind in blocker_kinds
    }
    windows_profile_files = {
        item.path
        for item in findings
        if classify_path(item.path) == "windows_profile"
    }
    score = max(0, min(100, 100 - len(core_blocker_files) * 6 - len(windows_profile_files)))
    status = "READY_WITH_PROFILES" if score >= 80 else ("NEEDS_SHIMS" if score >= 55 else "WINDOWS_FIRST")
    return {
        "status": status,
        "score": score,
        "findings_total": len(findings),
        "affected_files": len(affected_files),
        "pathlib_files": len(positive_files),
        "by_kind": dict(sorted(by_kind.items())),
        "by_profile": dict(sorted(by_profile.items())),
        "core_blocker_files": len(core_blocker_files),
        "windows_profile_files": len(windows_profile_files),
    }


def build_recommendations(summary: dict[str, object]) -> list[str]:
    recommendations = [
        "Keep Windows desktop/UIA/input/voice tools behind a windows_profile gate.",
        "Keep Code Map, Graph Map, Autonomy Pass, Nucleus Smoke, session audit, and tool routing as the Linux-first core.",
        "Prefer pathlib, sys.executable, and relative paths for all new scripts.",
        "Add bash equivalents only for stable PowerShell workflows, not for every old helper.",
        "When Linux Mate mirror starts, run MCP core first without desktop-control tools.",
    ]
    if int(summary.get("core_blocker_files") or 0) > 0:
        recommendations.insert(0, "Review core_candidate blockers before treating the Linux mirror as primary.")
    return recommendations


def run_readiness(paths: list[str] | None = None) -> dict[str, object]:
    roots = [Path(item) for item in (paths or ["ANA_MAX/tools", "ANA_MAX/dev_artifacts/scripts", "vscode_extension", "tests", "docs"])]
    findings: list[Finding] = []
    positives: list[Finding] = []
    for path in iter_text_files(roots):
        file_findings, file_positives = scan_file(path)
        findings.extend(file_findings)
        positives.extend(file_positives)

    summary = summarize(findings, positives)
    return {
        "schema": "ana.linux_readiness.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "host_platform": sys.platform,
        "summary": summary,
        "recommendations": build_recommendations(summary),
        "top_findings": [item.to_dict() for item in findings[:80]],
    }


def write_report(report: dict[str, object]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"linux_readiness_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def print_human(report: dict[str, object], report_path: Path | None = None) -> None:
    summary = report["summary"]
    assert isinstance(summary, dict)
    print(f"ANA Linux Readiness: {summary['status']} score={summary['score']}")
    print(
        f"findings={summary['findings_total']} files={summary['affected_files']} "
        f"core_blocker_files={summary['core_blocker_files']}"
    )
    print(f"by_profile={json.dumps(summary['by_profile'], ensure_ascii=False)}")
    for item in report["recommendations"]:
        print(f"- {item}")
    if report_path:
        print(f"report={report_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check future Linux/Mate readiness for ANA MAX Lab.")
    parser.add_argument("paths", nargs="*", help="Optional paths to scan.")
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    parser.add_argument("--no-write", action="store_true", help="Do not write a report file.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run_readiness(args.paths or None)
    report_path = None if args.no_write else write_report(report)
    if args.json:
        print(json.dumps({**report, "report": str(report_path) if report_path else None}, indent=2, ensure_ascii=False))
    else:
        print_human(report, report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
