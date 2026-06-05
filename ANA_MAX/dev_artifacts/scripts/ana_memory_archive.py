"""Archive old ANA checkpoint/REM files only with explicit confirmation."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
from collections import Counter
from typing import Any

import ana_memory_hygiene


ANA_ROOT = ana_memory_hygiene.ANA_ROOT
REPORT_DIR = ana_memory_hygiene.REPORT_DIR
CONFIRM_PHRASE = "ARCHIVE_OLD_MEMORY"


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_under_ana_root(rel_path: str) -> Path:
    path = (ANA_ROOT / rel_path).resolve()
    root = ANA_ROOT.resolve()
    if path != root and root not in path.parents:
        raise ValueError(f"path escapes ANA_ROOT: {rel_path}")
    return path


def build_archive_plan(keep_latest: int = ana_memory_hygiene.DEFAULT_KEEP_LATEST) -> dict[str, Any]:
    report = ana_memory_hygiene.build_report(keep_latest=keep_latest, include_plan=True)
    plan = report.get("archive_plan", {})
    moves = list(plan.get("checkpoints", [])) + list(plan.get("rem_sleep_reports", []))
    enriched = []
    for move in moves:
        source = _resolve_under_ana_root(move["source"])
        target = _resolve_under_ana_root(move["target"])
        enriched.append(
            {
                **move,
                "source_exists": source.exists(),
                "target_exists": target.exists(),
                "sha256": _sha256(source) if source.exists() else None,
            }
        )
    summary = summarize_moves(enriched)
    return {
        "schema": "ana.memory_archive.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "mode": "dry_run",
        "keep_latest": keep_latest,
        "archive_root": plan.get("archive_root"),
        "archive_date_basis": plan.get("archive_date_basis", "utc"),
        "total_moves": len(enriched),
        "summary": summary,
        "moves": enriched,
        "safety": {
            "default_dry_run": True,
            "apply_requires": f"--apply --confirm {CONFIRM_PHRASE}",
            "within_ana_root_only": True,
            "no_delete": True,
        },
    }


def summarize_moves(moves: list[dict[str, Any]]) -> dict[str, Any]:
    kinds: Counter[str] = Counter()
    total_bytes = 0
    missing_sources = 0
    existing_targets = 0
    for move in moves:
        source = str(move.get("source") or "")
        if source.startswith("docs/rem_sleep/"):
            kinds["rem_sleep_reports"] += 1
        elif source.startswith("docs/SESSION_CHECKPOINT_"):
            kinds["checkpoints"] += 1
        else:
            kinds["other"] += 1
        total_bytes += int(move.get("bytes") or 0)
        if move.get("source_exists") is False:
            missing_sources += 1
        if move.get("target_exists") is True:
            existing_targets += 1
    return {
        "by_kind": dict(sorted(kinds.items())),
        "bytes": total_bytes,
        "missing_sources": missing_sources,
        "existing_targets": existing_targets,
    }


def apply_archive(plan: dict[str, Any], confirm: str) -> dict[str, Any]:
    if confirm != CONFIRM_PHRASE:
        raise PermissionError(f"Refusing archive apply without --confirm {CONFIRM_PHRASE}")
    applied = []
    skipped = []
    for move in plan.get("moves", []):
        source = _resolve_under_ana_root(move["source"])
        target = _resolve_under_ana_root(move["target"])
        if not source.exists():
            skipped.append({**move, "reason": "source_missing"})
            continue
        if target.exists():
            skipped.append({**move, "reason": "target_exists"})
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
        applied.append({**move, "applied": True})
    return {
        **plan,
        "mode": "applied",
        "applied_count": len(applied),
        "skipped_count": len(skipped),
        "applied": applied,
        "skipped": skipped,
    }


def verify_archive(report: dict[str, Any]) -> dict[str, Any]:
    moves = report.get("applied") if report.get("mode") == "applied" else report.get("moves", [])
    verified = []
    failed = []
    for move in moves:
        source = _resolve_under_ana_root(move["source"])
        target = _resolve_under_ana_root(move["target"])
        expected_hash = move.get("sha256")
        actual_hash = _sha256(target) if target.exists() else None
        item = {
            "source": move["source"],
            "target": move["target"],
            "source_missing": not source.exists(),
            "target_exists": target.exists(),
            "sha256_ok": bool(expected_hash and actual_hash == expected_hash),
        }
        if item["source_missing"] and item["target_exists"] and item["sha256_ok"]:
            verified.append(item)
        else:
            failed.append(item)
    return {
        "schema": "ana.memory_archive.verify.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_mode": report.get("mode"),
        "status": "PASS" if not failed else "FAIL",
        "verified_count": len(verified),
        "failed_count": len(failed),
        "verified": verified[:20],
        "failed": failed[:20],
    }


def check_archive_readiness(report: dict[str, Any]) -> dict[str, Any]:
    moves = report.get("moves", [])
    failures = []
    warnings = []
    if report.get("mode") != "dry_run":
        failures.append("report_is_not_dry_run")
    if not isinstance(moves, list) or not moves:
        warnings.append("no_moves")
        moves = []
    for index, move in enumerate(moves):
        if move.get("source_exists") is not True:
            failures.append(f"source_missing:{index}:{move.get('source')}")
        if move.get("target_exists") is True:
            failures.append(f"target_exists:{index}:{move.get('target')}")
        if not move.get("sha256"):
            failures.append(f"missing_sha256:{index}:{move.get('source')}")
        try:
            _resolve_under_ana_root(str(move.get("source") or ""))
            _resolve_under_ana_root(str(move.get("target") or ""))
        except Exception:
            failures.append(f"path_escape:{index}")
    safety = report.get("safety", {}) if isinstance(report.get("safety"), dict) else {}
    if safety.get("default_dry_run") is not True:
        failures.append("safety_default_dry_run_not_true")
    if safety.get("no_delete") is not True:
        failures.append("safety_no_delete_not_true")
    if safety.get("within_ana_root_only") is not True:
        failures.append("safety_within_ana_root_only_not_true")
    return {
        "schema": "ana.memory_archive.readiness.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_mode": report.get("mode"),
        "archive_root": report.get("archive_root"),
        "archive_date_basis": report.get("archive_date_basis", "utc"),
        "total_moves": len(moves),
        "summary": report.get("summary", {}),
        "status": "FAIL" if failures else "PASS",
        "failures": failures[:20],
        "warnings": warnings[:20],
        "apply_command": f"python ANA_MAX/dev_artifacts/scripts/ana_memory_archive.py --keep-latest {report.get('keep_latest', ana_memory_hygiene.DEFAULT_KEEP_LATEST)} --apply --confirm {CONFIRM_PHRASE}",
        "safety": "Read-only readiness check. It does not move files.",
    }


def write_report(report: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"memory_archive_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dry-run or apply ANA memory archive plan.")
    parser.add_argument("--keep-latest", type=int, default=ana_memory_hygiene.DEFAULT_KEEP_LATEST)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    parser.add_argument("--verify-report", default="", help="Verify an applied archive report JSON")
    parser.add_argument("--readiness-report", default="", help="Check whether a dry-run archive report is ready to apply")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.readiness_report:
        loaded = json.loads(Path(args.readiness_report).read_text(encoding="utf-8"))
        report = check_archive_readiness(loaded)
    elif args.verify_report:
        loaded = json.loads(Path(args.verify_report).read_text(encoding="utf-8"))
        report = verify_archive(loaded)
    else:
        plan = build_archive_plan(keep_latest=max(1, args.keep_latest))
        report = apply_archive(plan, args.confirm) if args.apply else plan
    path = None if args.no_write else write_report(report)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        if args.verify_report:
            print(
                "ANA Memory Archive Verify: "
                f"{report['status']} verified={report['verified_count']} failed={report['failed_count']}"
            )
        elif args.readiness_report:
            summary = report.get("summary", {})
            by_kind = summary.get("by_kind", {}) if isinstance(summary, dict) else {}
            kind_text = ", ".join(f"{key}={value}" for key, value in by_kind.items()) or "-"
            print(
                "ANA Memory Archive Readiness: "
                f"{report['status']} moves={report['total_moves']} kinds={kind_text} "
                f"failures={len(report.get('failures', []))}"
            )
        else:
            summary = report.get("summary", {})
            by_kind = summary.get("by_kind", {})
            kind_text = ", ".join(f"{key}={value}" for key, value in by_kind.items()) or "-"
            print(
                "ANA Memory Archive: "
                f"mode={report['mode']} moves={report['total_moves']} "
                f"archive_root={report['archive_root']} "
                f"date_basis={report.get('archive_date_basis', 'utc')} "
                f"kinds={kind_text} bytes={summary.get('bytes', 0)}"
            )
            if args.apply:
                print(f"applied={report.get('applied_count', 0)} skipped={report.get('skipped_count', 0)}")
            else:
                print(f"apply_requires=--apply --confirm {CONFIRM_PHRASE}")
        if path:
            print(f"report={path}")
    return 0 if report.get("status", "PASS") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
