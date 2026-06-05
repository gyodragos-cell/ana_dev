"""Report lab memory/checkpoint hygiene without moving or deleting files."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
REPORT_DIR = ANA_ROOT / "dev_artifacts" / "reports"
ARCHIVE_DIR = ANA_ROOT / "dev_artifacts" / "archives"
DEFAULT_KEEP_LATEST = 20


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _items(path: Path, pattern: str) -> list[Path]:
    if not path.exists():
        return []
    return sorted(path.glob(pattern), key=lambda item: item.name)


def _summarize_files(files: list[Path], keep_latest: int) -> dict:
    total_bytes = sum(path.stat().st_size for path in files if path.exists())
    latest = sorted(files, key=lambda item: item.name, reverse=True)[:keep_latest]
    archive_candidates = max(0, len(files) - keep_latest)
    return {
        "count": len(files),
        "total_bytes": total_bytes,
        "keep_latest": keep_latest,
        "archive_candidates": archive_candidates,
        "latest": [
            {
                "name": path.name,
                "bytes": path.stat().st_size,
            }
            for path in latest
        ],
    }


def _archive_candidates(files: list[Path], keep_latest: int) -> list[Path]:
    ordered = sorted(files, key=lambda item: item.name, reverse=True)
    return sorted(ordered[keep_latest:], key=lambda item: item.name)


def _plan_moves(files: list[Path], keep_latest: int, archive_root: Path, section: str) -> list[dict]:
    target_dir = archive_root / section
    moves = []
    for path in _archive_candidates(files, keep_latest):
        moves.append(
            {
                "source": path.relative_to(ANA_ROOT).as_posix(),
                "target": (target_dir / path.name).relative_to(ANA_ROOT).as_posix(),
                "bytes": path.stat().st_size,
            }
        )
    return moves


def build_report(keep_latest: int = DEFAULT_KEEP_LATEST, include_plan: bool = False) -> dict:
    checkpoints = _items(ANA_ROOT / "docs", "SESSION_CHECKPOINT_*.md")
    rem_reports = _items(ANA_ROOT / "docs" / "rem_sleep", "REM_SLEEP_REPORT_*.md")
    checkpoint_summary = _summarize_files(checkpoints, keep_latest)
    rem_summary = _summarize_files(rem_reports, keep_latest)
    archive_candidates = checkpoint_summary["archive_candidates"] + rem_summary["archive_candidates"]
    report = {
        "schema": "ana.memory_hygiene.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mode": "archive_plan" if include_plan else "report_only",
        "keep_latest": keep_latest,
        "checkpoints": checkpoint_summary,
        "rem_sleep_reports": rem_summary,
        "archive_candidates": archive_candidates,
        "recommended_next_step": (
            "Archive older checkpoint/REM files into a dated lab archive after a final REM consolidation."
            if archive_candidates
            else "No archive action needed."
        ),
        "safety": "Read-only report. No files were moved, deleted, or modified.",
    }
    if include_plan:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        archive_root = ARCHIVE_DIR / f"memory_hygiene_{stamp}"
        checkpoint_moves = _plan_moves(checkpoints, keep_latest, archive_root, "checkpoints")
        rem_moves = _plan_moves(rem_reports, keep_latest, archive_root, "rem_sleep")
        report["archive_plan"] = {
            "archive_root": archive_root.relative_to(ANA_ROOT).as_posix(),
            "archive_date_basis": "utc",
            "checkpoints": checkpoint_moves,
            "rem_sleep_reports": rem_moves,
            "total_moves": len(checkpoint_moves) + len(rem_moves),
            "apply_supported": False,
            "apply_note": "This script is dry-run only. Add an explicit reviewed archive command before moving files.",
        }
    return report


def write_report(report: dict) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"memory_hygiene_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report ANA lab memory/checkpoint hygiene.")
    parser.add_argument("--keep-latest", type=int, default=DEFAULT_KEEP_LATEST)
    parser.add_argument("--plan", action="store_true", help="Include a dry-run archive plan")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(keep_latest=max(1, args.keep_latest), include_plan=args.plan)
    path = None if args.no_write else write_report(report)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(
            "ANA Memory Hygiene: "
            f"checkpoints={report['checkpoints']['count']} "
            f"rem={report['rem_sleep_reports']['count']} "
            f"archive_candidates={report['archive_candidates']}"
        )
        print(f"next_action={report['recommended_next_step']}")
        if args.plan:
            plan = report.get("archive_plan", {})
            print(
                "archive_plan="
                f"{plan.get('total_moves', 0)} moves -> {plan.get('archive_root')} "
                f"date_basis={plan.get('archive_date_basis', 'utc')}"
            )
        if path:
            print(f"report={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
