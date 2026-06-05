"""Summarize local ANA voice/chat conversation evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
if str(ANA_ROOT) not in sys.path:
    sys.path.insert(0, str(ANA_ROOT))

from tools.conversation_audit import summarize_conversation_audit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize ANA conversation audit JSONL.")
    parser.add_argument("--hours", type=int, default=24, help="Recent hours to inspect.")
    parser.add_argument("--limit", type=int, default=80, help="Maximum events to summarize.")
    parser.add_argument("--json", action="store_true", help="Print the full summary as JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = summarize_conversation_audit(hours=args.hours, limit=args.limit)
    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0

    sources = ", ".join(f"{key}={value}" for key, value in summary["sources"].items()) or "none"
    print(
        "ANA Conversation Audit: "
        f"{summary['status']} events={summary['events']} "
        f"spoken={summary['spoken_events']} skipped={summary['sensitive_skipped']} "
        f"sources={sources}"
    )
    print(f"message={summary['message']}")
    print(f"path={summary['path']}")
    if summary["latest"]:
        print("latest:")
        for entry in summary["latest"][-5:]:
            text = str(entry.get("text") or "[skipped]")
            print(f"- {entry.get('ts')} {entry.get('source')}: {text[:160]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
