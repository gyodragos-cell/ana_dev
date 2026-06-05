"""Save a session checkpoint through local source, bypassing stale live MCP.

Use this when the live MCP server has not reloaded yet and the running
`session_checkpoint` tool may still use older behavior.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(ANA_ROOT) not in sys.path:
    sys.path.insert(0, str(ANA_ROOT))

import ana_memory_archive
from tools.session_checkpoint_tool import SessionCheckpointTool


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def result_to_dict(result: Any) -> dict[str, Any]:
    return {
        "success": bool(getattr(result, "is_success", False)),
        "data": getattr(result, "data", None),
        "message": getattr(result, "message", ""),
        "error": getattr(result, "error", None),
    }


def save_checkpoint(args: argparse.Namespace) -> dict[str, Any]:
    result = SessionCheckpointTool().execute(
        title=args.title,
        summary=args.summary,
        current_goal=args.current_goal,
        next_steps=args.next_steps,
        files_changed=args.files_changed,
        validation=args.validation,
        risks=args.risks,
        sync_status=args.sync_status,
        include_git=args.include_git,
    )
    payload = result_to_dict(result)
    if payload["success"] and args.refresh_memory_archive:
        plan = ana_memory_archive.build_archive_plan()
        archive_path = ana_memory_archive.write_report(plan)
        data = payload.get("data")
        if not isinstance(data, dict):
            data = {}
            payload["data"] = data
        data["memory_archive_refresh"] = {
            "mode": plan.get("mode"),
            "total_moves": plan.get("total_moves"),
            "archive_date_basis": plan.get("archive_date_basis", "utc"),
            "report": str(archive_path),
        }
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Save checkpoint through local source instead of live MCP.")
    parser.add_argument("--title", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--current-goal", default="")
    parser.add_argument("--next-steps", default="")
    parser.add_argument("--files-changed", default="")
    parser.add_argument("--validation", default="")
    parser.add_argument("--risks", default="")
    parser.add_argument("--sync-status", default="")
    parser.add_argument("--include-git", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--refresh-memory-archive", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = save_checkpoint(args)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        status = "PASS" if payload["success"] else "FAIL"
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        print(f"ANA Local Checkpoint: {status} {payload.get('message') or payload.get('error') or ''}".rstrip())
        if data.get("path"):
            print(f"path={data['path']}")
        refresh = data.get("memory_archive_refresh") if isinstance(data, dict) else None
        if isinstance(refresh, dict):
            print(
                "memory_archive_refresh="
                f"{refresh.get('mode')} moves={refresh.get('total_moves')} "
                f"date_basis={refresh.get('archive_date_basis')} report={refresh.get('report')}"
            )
    return 0 if payload["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
