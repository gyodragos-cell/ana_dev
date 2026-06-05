"""Tail ANA conversation audit in real time for the Live Console."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
AUDIT_FILE = ANA_ROOT / "memory" / "conversation_audit.jsonl"


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def compact_text(text: str, limit: int = 180) -> str:
    cleaned = " ".join(str(text or "").replace("\r", " ").replace("\n", " ").split())
    if not cleaned:
        return "[skipped]"
    return cleaned if len(cleaned) <= limit else f"{cleaned[: limit - 3]}..."


def format_entry(entry: dict[str, Any]) -> str:
    ts = str(entry.get("ts") or "")
    source = str(entry.get("source") or "unknown")
    spoken = "yes" if entry.get("spoken") else "no"
    skipped = " skipped=yes" if entry.get("sensitive_skipped") else ""
    text = compact_text(str(entry.get("text") or ""))
    return f"{ts} source={source} spoken={spoken}{skipped} text={text}"


def parse_line(line: str) -> str:
    try:
        entry = json.loads(line)
    except json.JSONDecodeError:
        return f"invalid-json text={compact_text(line)}"
    if not isinstance(entry, dict):
        return "invalid-entry"
    return format_entry(entry)


def tail_file(path: Path, *, poll: float, from_start: bool) -> int:
    print(f"Conversation audit live tail active: {path}", flush=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        if not from_start:
            handle.seek(0, 2)
        while True:
            line = handle.readline()
            if not line:
                time.sleep(max(0.1, float(poll)))
                continue
            line = line.strip()
            if line:
                print(parse_line(line), flush=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tail ANA conversation audit JSONL.")
    parser.add_argument("--path", default=str(AUDIT_FILE), help="JSONL audit path.")
    parser.add_argument("--poll", type=float, default=0.5, help="Polling interval in seconds.")
    parser.add_argument("--from-start", action="store_true", help="Print existing events before tailing.")
    parser.add_argument("--format-line", default="", help="Format one JSONL line and exit; test helper.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.format_line:
        print(parse_line(args.format_line))
        return 0
    return tail_file(Path(args.path), poll=args.poll, from_start=args.from_start)


if __name__ == "__main__":
    raise SystemExit(main())
