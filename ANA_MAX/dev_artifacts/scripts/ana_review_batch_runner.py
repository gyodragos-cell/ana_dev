"""Run or preview the focused commands suggested by Dirty Tree review batches."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
from typing import Any

import ana_dirty_tree_report


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
REPORT_DIR = ANA_ROOT / "dev_artifacts" / "reports"


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def tail(text: str, max_chars: int = 3000) -> str:
    text = str(text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def active_review_batches(limit: int = 12) -> list[dict[str, Any]]:
    report = ana_dirty_tree_report.build_report(limit=limit)
    active = report.get("active_work") if isinstance(report, dict) else {}
    batches = active.get("review_batches") if isinstance(active, dict) else []
    if not isinstance(batches, list):
        return []
    return [batch for batch in batches if isinstance(batch, dict)]


def select_batch(batches: list[dict[str, Any]], category: str | None) -> dict[str, Any]:
    if not batches:
        raise RuntimeError("No active work review batches found.")
    if not category:
        return batches[0]
    for batch in batches:
        if batch.get("category") == category:
            return batch
    available = ", ".join(str(batch.get("category")) for batch in batches)
    raise RuntimeError(f"Review batch '{category}' not found. Available: {available}")


def selected_commands(batch: dict[str, Any], command_index: int, all_commands: bool) -> list[str]:
    commands = batch.get("suggested_commands")
    if not isinstance(commands, list):
        return []
    normalized = [str(command) for command in commands if str(command).strip()]
    if all_commands:
        return normalized
    if not normalized:
        return []
    if command_index < 0 or command_index >= len(normalized):
        raise RuntimeError(f"Command index {command_index} out of range for batch '{batch.get('category')}'.")
    return [normalized[command_index]]


def command_to_argv(command: str) -> list[str]:
    if any(token in command for token in (";", "&", "|", ">", "<", "`")):
        raise RuntimeError(f"Rejected command with shell metacharacters: {command}")
    try:
        argv = shlex.split(command, posix=False)
    except ValueError as exc:
        raise RuntimeError(f"Could not parse suggested command: {exc}") from exc
    if not argv:
        raise RuntimeError("Empty suggested command.")
    executable = Path(argv[0]).name.lower()
    if executable not in {"python", "python.exe", "py", "py.exe"}:
        raise RuntimeError(f"Only Python review commands are allowed, got: {argv[0]}")
    argv[0] = sys.executable
    return argv


def run_one(command: str, *, execute: bool, timeout: int) -> dict[str, Any]:
    argv = command_to_argv(command)
    result: dict[str, Any] = {
        "command": command,
        "argv": argv,
        "status": "planned",
        "returncode": None,
        "elapsed_ms": 0,
        "stdout_tail": "",
        "stderr_tail": "",
    }
    if not execute:
        return result

    started = time.perf_counter()
    try:
        completed = subprocess.run(
            argv,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        result.update({
            "status": "timeout",
            "elapsed_ms": int((time.perf_counter() - started) * 1000),
            "stdout_tail": tail(exc.stdout or ""),
            "stderr_tail": tail(exc.stderr or ""),
        })
        return result

    result.update({
        "status": "pass" if completed.returncode == 0 else "fail",
        "returncode": completed.returncode,
        "elapsed_ms": int((time.perf_counter() - started) * 1000),
        "stdout_tail": tail(completed.stdout),
        "stderr_tail": tail(completed.stderr),
    })
    return result


def build_report(
    *,
    category: str | None = None,
    command_index: int = 0,
    all_commands: bool = False,
    all_batches: bool = False,
    execute: bool = False,
    timeout: int = 120,
    limit: int = 12,
) -> dict[str, Any]:
    batches = active_review_batches(limit=limit)
    if all_batches and execute:
        raise RuntimeError("All-batches mode is plan-only. Select one category before using --run.")
    if all_batches:
        command_results: list[dict[str, Any]] = []
        for batch in batches:
            for command in selected_commands(batch, 0, True):
                result = run_one(command, execute=False, timeout=timeout)
                result["category"] = batch.get("category")
                command_results.append(result)
        return {
            "schema": "ana.review_batch_runner.v1",
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": "DRY_RUN",
            "mode": "dry_run",
            "category": "all",
            "batch": None,
            "batches": [
                {
                    "category": batch.get("category"),
                    "count": batch.get("count"),
                    "tracked": batch.get("tracked"),
                    "untracked": batch.get("untracked"),
                    "sample": (batch.get("sample") or [])[:8],
                    "next_step": batch.get("next_step"),
                    "suggested_commands": (batch.get("suggested_commands") or [])[:3],
                }
                for batch in batches
            ],
            "available_batches": [batch.get("category") for batch in batches],
            "commands": command_results,
            "policy": {
                "dry_run_default": True,
                "all_batches_plan_only": True,
                "shell": False,
                "allowed_source": "ana_dirty_tree_report.active_work.review_batches.suggested_commands",
                "destructive_actions": False,
                "archives_or_deletes_files": False,
            },
        }
    batch = select_batch(batches, category)
    commands = selected_commands(batch, command_index, all_commands)
    command_results = [
        run_one(command, execute=execute, timeout=timeout)
        for command in commands
    ]
    statuses = [item["status"] for item in command_results]
    status = "PASS"
    if any(item == "fail" for item in statuses):
        status = "FAIL"
    elif any(item == "timeout" for item in statuses):
        status = "WARN"
    elif not execute:
        status = "DRY_RUN"
    return {
        "schema": "ana.review_batch_runner.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": status,
        "mode": "run" if execute else "dry_run",
        "category": batch.get("category"),
        "batch": {
            "category": batch.get("category"),
            "count": batch.get("count"),
            "tracked": batch.get("tracked"),
            "untracked": batch.get("untracked"),
            "sample": (batch.get("sample") or [])[:8],
            "next_step": batch.get("next_step"),
        },
        "available_batches": [batch.get("category") for batch in batches],
        "commands": command_results,
        "policy": {
            "dry_run_default": True,
            "shell": False,
            "allowed_source": "ana_dirty_tree_report.active_work.review_batches.suggested_commands",
            "destructive_actions": False,
            "archives_or_deletes_files": False,
        },
    }


def write_report(report: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / review_report_filename(report)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    return path


def review_report_filename(report: dict[str, Any]) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    unique = f"{os.getpid()}_{time.time_ns() % 1_000_000_000:09d}"
    mode = safe_filename_token(str(report.get("mode") or "unknown"))
    category = safe_filename_token(str(report.get("category") or "unknown"))
    return f"review_batch_runner_{stamp}_{unique}_{mode}_{category}.json"


def safe_filename_token(value: str) -> str:
    token = re.sub(r"[^a-zA-Z0-9_.-]+", "_", value.strip())
    return token.strip("._-") or "unknown"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preview or run focused Dirty Tree review-batch commands.")
    parser.add_argument("--category", help="Review batch category. Defaults to the first active batch.")
    parser.add_argument("--command-index", type=int, default=0, help="Suggested command index to run or preview.")
    parser.add_argument("--all", action="store_true", help="Use all suggested commands from the selected batch.")
    parser.add_argument("--all-batches", action="store_true", help="Preview suggested commands from all active batches. Plan-only.")
    parser.add_argument("--run", action="store_true", help="Actually execute the selected command(s). Default is dry-run.")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.all_batches and args.run:
        raise SystemExit("--all-batches is plan-only. Select --category before using --run.")
    report = build_report(
        category=args.category,
        command_index=args.command_index,
        all_commands=args.all,
        all_batches=args.all_batches,
        execute=args.run,
        timeout=max(1, args.timeout),
        limit=max(1, args.limit),
    )
    path = None if args.no_write else write_report(report)
    if path:
        report["report"] = str(path)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(
            "ANA Review Batch: "
            f"status={report['status']} mode={report['mode']} category={report['category']} "
            f"commands={len(report['commands'])}"
        )
        for index, item in enumerate(report["commands"]):
            category_prefix = f"{item.get('category')} " if item.get("category") else ""
            print(f"[{index}] {category_prefix}{item['status']} {item['command']}")
        if path:
            print(f"report={path}")

    if args.run and any(item["status"] in {"fail", "timeout"} for item in report["commands"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
