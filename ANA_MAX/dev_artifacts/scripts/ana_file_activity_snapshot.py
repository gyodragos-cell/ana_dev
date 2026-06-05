"""Detect aggregate file activity for an authorized local root.

This is a privacy-preserving snapshot diff, not a live keylogger or content
scanner. It records relative paths, sizes, mtimes, suffixes, and stat digests so
ANA can notice created/deleted/modified files between runs.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
MEMORY_DIR = ANA_ROOT / "memory" / "file_activity"
REPORT_DIR = ANA_ROOT / "dev_artifacts" / "reports"

DEFAULT_SKIP_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "venv",
}
DEFAULT_SKIP_REL_PREFIXES = {
    "ANA_MAX/dev_artifacts/archives",
    "ANA_MAX/dev_artifacts/audit",
    "ANA_MAX/dev_artifacts/reports",
    "ANA_MAX/data",
    "ANA_MAX/logs",
    "ANA_MAX/memory",
    "ANA_MAX/screenshots",
    "screenshots",
}


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_root_label(root: Path) -> str:
    text = str(root.resolve())
    return text.replace(str(REPO_ROOT), "$WORKSPACE").replace(str(ANA_ROOT), "$ANA_MAX")


def root_id(root: Path) -> str:
    return sha256_text(str(root.resolve()).lower())[:16]


def should_skip(path: Path, root: Path) -> bool:
    parts = set(path.parts)
    if parts & DEFAULT_SKIP_DIR_NAMES:
        return True
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        return True
    return any(rel == prefix or rel.startswith(prefix + "/") for prefix in DEFAULT_SKIP_REL_PREFIXES)


def stat_entry(path: Path, root: Path) -> dict[str, Any] | None:
    try:
        stat = path.stat()
        rel = path.relative_to(root).as_posix()
    except OSError:
        return None
    payload = {
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "suffix": path.suffix.lower()[:20],
    }
    payload["stat_digest"] = sha256_text(json.dumps(payload, sort_keys=True, ensure_ascii=True))
    return {"path": rel, **payload}


def scan_root(root: Path, max_files: int = 20000) -> dict[str, dict[str, Any]]:
    root = root.resolve()
    manifest: dict[str, dict[str, Any]] = {}
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Root not found or not a directory: {root}")
    for path in root.rglob("*"):
        if len(manifest) >= max_files:
            break
        if should_skip(path, root):
            continue
        if not path.is_file():
            continue
        entry = stat_entry(path, root)
        if entry:
            manifest[entry["path"]] = entry
    return dict(sorted(manifest.items()))


def load_baseline(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def diff_manifests(old: dict[str, dict[str, Any]], new: dict[str, dict[str, Any]], limit: int = 50) -> dict[str, Any]:
    old_paths = set(old)
    new_paths = set(new)
    created = sorted(new_paths - old_paths)
    deleted = sorted(old_paths - new_paths)
    modified = sorted(
        path
        for path in old_paths & new_paths
        if old[path].get("stat_digest") != new[path].get("stat_digest")
    )

    def sample(paths: list[str]) -> list[dict[str, Any]]:
        return [{"path": path, "suffix": (new.get(path) or old.get(path) or {}).get("suffix")} for path in paths[:limit]]

    return {
        "created": len(created),
        "deleted": len(deleted),
        "modified": len(modified),
        "samples": {
            "created": sample(created),
            "deleted": sample(deleted),
            "modified": sample(modified),
        },
    }


def build_report(root: Path, max_files: int = 20000, sample_limit: int = 50) -> tuple[dict[str, Any], dict[str, Any]]:
    root = root.resolve()
    manifest = scan_root(root, max_files=max_files)
    baseline_path = MEMORY_DIR / f"baseline_{root_id(root)}.json"
    baseline = load_baseline(baseline_path)
    old_manifest = baseline.get("manifest", {}) if isinstance(baseline, dict) else {}
    diff = diff_manifests(old_manifest, manifest, limit=sample_limit)
    report = {
        "schema": "ana.file_activity_snapshot.v1",
        "generated_at": now_iso(),
        "root": safe_root_label(root),
        "root_id": root_id(root),
        "baseline_available": bool(baseline),
        "files_scanned": len(manifest),
        "max_files": max_files,
        "diff": diff,
        "privacy": {
            "content_read": False,
            "raw_private_payloads": False,
            "paths": "relative_to_authorized_root",
        },
        "next_action": (
            "Review aggregate file activity if unexpected deletes/modifies appear."
            if baseline and (diff["created"] or diff["deleted"] or diff["modified"])
            else "Baseline initialized or no file activity detected."
        ),
    }
    baseline_payload = {
        "schema": "ana.file_activity_baseline.v1",
        "generated_at": report["generated_at"],
        "root": report["root"],
        "root_id": report["root_id"],
        "manifest": manifest,
    }
    return report, baseline_payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_report(report: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"file_activity_snapshot_{stamp}.json"
    write_json(path, report)
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report aggregate file activity for an authorized root.")
    parser.add_argument("--root", default=str(REPO_ROOT), help="Authorized root to scan; default is workspace root")
    parser.add_argument("--max-files", type=int, default=20000)
    parser.add_argument("--sample-limit", type=int, default=50)
    parser.add_argument("--no-update", action="store_true", help="Do not update the baseline manifest")
    parser.add_argument("--no-write", action="store_true", help="Do not write report or baseline")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).expanduser()
    report, baseline = build_report(
        root=root,
        max_files=max(1, args.max_files),
        sample_limit=max(1, args.sample_limit),
    )
    report_path = None
    if not args.no_write:
        report_path = write_report(report)
        if not args.no_update:
            write_json(MEMORY_DIR / f"baseline_{report['root_id']}.json", baseline)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        diff = report["diff"]
        print(
            "ANA File Activity: "
            f"baseline={report['baseline_available']} "
            f"scanned={report['files_scanned']} "
            f"created={diff['created']} "
            f"deleted={diff['deleted']} "
            f"modified={diff['modified']}"
        )
        print(f"next_action={report['next_action']}")
        if report_path:
            print(f"report={report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
