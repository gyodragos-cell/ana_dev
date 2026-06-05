"""Read-only dirty tree classifier for ANA lab work."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
REPORT_DIR = ANA_ROOT / "dev_artifacts" / "reports"


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def git_status_lines() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git status failed")
    return [line for line in result.stdout.splitlines() if line.strip()]


def normalize_path(line: str) -> tuple[str, str]:
    status = line[:2].strip() or "?"
    path = line[3:].strip() if len(line) > 3 else line.strip()
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return status, path.replace("\\", "/")


def classify(path: str) -> str:
    if path == "ANA_MAX/docs/CURRENT_SESSION_HANDOFF.md":
        return "checkpoint"
    if path.startswith("ANA_MAX/docs/SESSION_CHECKPOINT_"):
        return "checkpoint"
    if path.startswith("ANA_MAX/docs/rem_sleep/"):
        return "rem_sleep"
    if path.startswith("ANA_MAX/dev_artifacts/reports/"):
        return "report"
    if path.startswith("ANA_MAX/dev_artifacts/archives/"):
        return "archive"
    if path.endswith(".vsix") or "/vsix_build_" in path or "/vsix_verify_" in path:
        return "vsix_artifact"
    if path.startswith("tests/"):
        return "test"
    if path.startswith("docs/") or path.endswith(".md"):
        return "doc"
    if path.startswith("vscode_extension/"):
        return "extension"
    if path.startswith("ANA_MAX/tools/") or path.startswith("ANA_MAX/core/") or path in {
        "ANA_MAX/main.py",
        "ANA_MAX/mcp_stdio.py",
        "ANA_MAX/test_all_tools.py",
    }:
        return "runtime"
    if path.startswith("ANA_MAX/dev_artifacts/scripts/"):
        return "script"
    if path.startswith("ANA_MAX/config/"):
        return "config"
    if path.startswith("ANA_MAX/memory/") or path.endswith(".db"):
        return "memory"
    return "other"


def top_folder(path: str) -> str:
    parts = path.split("/")
    if len(parts) >= 2 and parts[0] == "ANA_MAX":
        return "/".join(parts[:2])
    return parts[0] if parts else ""


def grouped_samples(entries: list[dict[str, str]], limit: int = 8) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for entry in entries:
        category = entry["category"]
        bucket = grouped.setdefault(
            category,
            {
                "count": 0,
                "tracked": 0,
                "untracked": 0,
                "top_folders": {},
                "sample": [],
            },
        )
        bucket["count"] += 1
        if entry["status"] == "??":
            bucket["untracked"] += 1
        else:
            bucket["tracked"] += 1
        top = entry["top_folder"]
        bucket["top_folders"][top] = bucket["top_folders"].get(top, 0) + 1
        if len(bucket["sample"]) < limit:
            bucket["sample"].append(entry["path"])

    for bucket in grouped.values():
        bucket["top_folders"] = dict(
            sorted(bucket["top_folders"].items(), key=lambda item: (-item[1], item[0]))[:limit]
        )
    return dict(sorted(grouped.items()))


def review_batches(grouped: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    priority = [
        (
            "runtime",
            "Run focused runtime tests and inspect owning modules first.",
            [
                "python -m compileall -q ANA_MAX/core ANA_MAX/tools ANA_MAX/main.py ANA_MAX/mcp_stdio.py",
                "python -m pytest tests/runtime/test_tool_router_tool.py tests/runtime/test_agent_coach_recommend.py tests/runtime/test_error_radar_tool.py tests/runtime/test_tool_healthcheck_tool.py -q",
            ],
        ),
        (
            "script",
            "Run focused script tests or dry-run CLIs before relying on automation.",
            [
                "python -m compileall -q ANA_MAX/dev_artifacts/scripts",
                "python -m pytest tests/runtime/test_ana_dirty_tree_report.py tests/runtime/test_ana_patch_advisor.py tests/runtime/test_ana_autonomy_runner.py -q",
            ],
        ),
        (
            "test",
            "Keep tests paired with the runtime/script behavior they verify.",
            [
                "python -m pytest tests/runtime -q",
            ],
        ),
        (
            "config",
            "Review policy/profile/permission effects before reload or packaging.",
            [
                "python ANA_MAX/dev_artifacts/scripts/ana_permission_manifest_coverage.py --no-write",
                "python ANA_MAX/dev_artifacts/scripts/ana_governance_check.py",
            ],
        ),
        (
            "extension",
            "Run extension syntax/version checks before packaging VSIX.",
            [
                "python ANA_MAX/dev_artifacts/scripts/ana_vsix_version_check.py",
                "python ANA_MAX/dev_artifacts/scripts/package_cockpit_vsix.py",
            ],
        ),
        (
            "doc",
            "Check docs describe current behavior without leaking lab-only state.",
            [
                "python ANA_MAX/dev_artifacts/scripts/ana_governance_check.py",
            ],
        ),
    ]
    batches: list[dict[str, Any]] = []
    for category, next_step, commands in priority:
        bucket = grouped.get(category)
        if not bucket:
            continue
        batches.append({
            "category": category,
            "count": bucket.get("count", 0),
            "tracked": bucket.get("tracked", 0),
            "untracked": bucket.get("untracked", 0),
            "sample": bucket.get("sample", []),
            "next_step": next_step,
            "suggested_commands": commands,
        })
    return batches


def build_report(limit: int = 12) -> dict[str, Any]:
    entries = []
    for line in git_status_lines():
        status, path = normalize_path(line)
        entries.append({
            "status": status,
            "path": path,
            "category": classify(path),
            "top_folder": top_folder(path),
        })
    categories = Counter(entry["category"] for entry in entries)
    statuses = Counter(entry["status"] for entry in entries)
    folders = Counter(entry["top_folder"] for entry in entries)
    active_categories = {"runtime", "script", "extension", "test", "config", "doc"}
    active = [entry for entry in entries if entry["category"] in active_categories]
    generated = [entry for entry in entries if entry["category"] not in active_categories]
    active_counts = Counter(entry["category"] for entry in active)
    generated_counts = Counter(entry["category"] for entry in generated)
    active_by_category = grouped_samples(active, limit=limit)
    generated_by_category = grouped_samples(generated, limit=limit)
    return {
        "schema": "ana.dirty_tree_report.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total": len(entries),
        "tracked": sum(1 for entry in entries if entry["status"] != "??"),
        "untracked": sum(1 for entry in entries if entry["status"] == "??"),
        "categories": dict(sorted(categories.items())),
        "statuses": dict(sorted(statuses.items())),
        "top_folders": dict(folders.most_common(limit)),
        "active_work": {
            "count": len(active),
            "categories": dict(sorted(active_counts.items())),
            "by_category": active_by_category,
            "review_batches": review_batches(active_by_category),
            "sample": [entry["path"] for entry in active[:limit]],
            "next_step": "Review this group as real work: runtime/scripts/tests/docs/config/extension.",
        },
        "generated_or_memory": {
            "count": len(generated),
            "categories": dict(sorted(generated_counts.items())),
            "by_category": generated_by_category,
            "sample": [entry["path"] for entry in generated[:limit]],
            "next_step": "Archive only generated checkpoint/REM/report noise after explicit operator confirmation.",
        },
        "recommendation": build_recommendation(categories, len(entries)),
        "safety": "Read-only git status classifier. It does not add, commit, archive, delete, or modify files.",
    }


def build_recommendation(categories: Counter[str], total: int) -> str:
    if total == 0:
        return "Dirty tree is clean. Continue with one scoped action."
    if categories.get("checkpoint", 0) > 50 or categories.get("rem_sleep", 0) > 20:
        return "Do not commit blindly. Review active work first, then archive checkpoint/REM noise only with explicit operator approval."
    if total > 50:
        return "Group active code/docs/tests separately before commit or archive work."
    return "Review changed paths, then continue with scoped verification."


def write_report(report: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"dirty_tree_report_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Classify ANA lab dirty tree without mutating files.")
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(limit=max(1, args.limit))
    path = None if args.no_write else write_report(report)
    if args.json:
        print(json.dumps({**report, "report": str(path) if path else None}, indent=2, ensure_ascii=False))
    else:
        cats = ", ".join(f"{key}={value}" for key, value in report["categories"].items())
        print(
            "ANA Dirty Tree: "
            f"total={report['total']} tracked={report['tracked']} untracked={report['untracked']} "
            f"categories={cats}"
        )
        print(
            "active_work="
            f"{report['active_work']['count']} "
            f"categories={report['active_work']['categories']}"
        )
        print(
            "generated_or_memory="
            f"{report['generated_or_memory']['count']} "
            f"categories={report['generated_or_memory']['categories']}"
        )
        print(f"recommendation={report['recommendation']}")
        if path:
            print(f"report={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
