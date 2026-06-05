"""End-to-end smoke for ANA Voice Operator Mode.

The smoke writes one unique phrase into the ANA voice queue, waits for the
chat voice bridge to consume it, then verifies that conversation audit recorded
the spoken queue event. It does not prove the human heard the audio; it proves
the local operator pipeline is alive and auditable.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
QUEUE_FILE = ANA_ROOT / "voice_queue.txt"
AUDIT_FILE = ANA_ROOT / "memory" / "conversation_audit.jsonl"

if str(ANA_ROOT) not in sys.path:
    sys.path.insert(0, str(ANA_ROOT))

from tools.conversation_audit import read_conversation_entries


def timestamp_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_phrase(label: str = "") -> str:
    suffix = label.strip() or timestamp_id()
    return f"ANA voice operator smoke {suffix}. O singura voce principala. Audit live confirmat."


def append_queue_phrase(phrase: str, queue_path: Path = QUEUE_FILE) -> None:
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{phrase}\n")


def find_audit_phrase(phrase: str, audit_path: Path = AUDIT_FILE, *, hours: int = 1, limit: int = 200) -> dict[str, Any] | None:
    for entry in reversed(read_conversation_entries(hours=hours, limit=limit, path=audit_path)):
        text = str(entry.get("text") or "")
        if phrase in text and str(entry.get("source") or "") == "voice_queue":
            return entry
    return None


def wait_for_audit_phrase(
    phrase: str,
    audit_path: Path = AUDIT_FILE,
    *,
    timeout_sec: float = 12,
    poll_sec: float = 0.5,
) -> dict[str, Any] | None:
    deadline = time.time() + max(1.0, float(timeout_sec))
    while time.time() < deadline:
        found = find_audit_phrase(phrase, audit_path)
        if found:
            return found
        time.sleep(max(0.1, float(poll_sec)))
    return None


def run_smoke(args: argparse.Namespace) -> dict[str, Any]:
    phrase = args.phrase or build_phrase(args.label)
    if not args.no_write:
        append_queue_phrase(phrase, Path(args.queue_path))
    found = None if args.no_write else wait_for_audit_phrase(
        phrase,
        Path(args.audit_path),
        timeout_sec=args.timeout,
        poll_sec=args.poll,
    )
    status = "PASS" if found else ("DRY_RUN" if args.no_write else "WARN")
    return {
        "schema": "ana.voice_operator_smoke.v1",
        "status": status,
        "success": status == "PASS",
        "phrase": phrase,
        "queue_path": str(Path(args.queue_path)),
        "audit_path": str(Path(args.audit_path)),
        "queue_written": not args.no_write,
        "audit_seen": bool(found),
        "event": found or None,
        "message": (
            "Voice operator smoke PASS: queue event was audited."
            if found
            else "Voice operator smoke WARN: queue event was not audited before timeout."
            if not args.no_write
            else "Voice operator smoke DRY_RUN: no queue write performed."
        ),
        "next_action": (
            "Ask the operator whether the phrase was heard as one clean voice."
            if found
            else "Open ANA Live Console, ensure chat_voice_bridge.py is running, then rerun smoke."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Smoke test ANA voice operator queue -> voice bridge -> audit.")
    parser.add_argument("--label", default="", help="Optional phrase suffix.")
    parser.add_argument("--phrase", default="", help="Exact phrase to send.")
    parser.add_argument("--timeout", type=float, default=12, help="Seconds to wait for audit evidence.")
    parser.add_argument("--poll", type=float, default=0.5, help="Polling interval.")
    parser.add_argument("--queue-path", default=str(QUEUE_FILE))
    parser.add_argument("--audit-path", default=str(AUDIT_FILE))
    parser.add_argument("--no-write", action="store_true", help="Do not write to voice queue.")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run_smoke(args)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(
            "ANA Voice Operator Smoke: "
            f"{report['status']} audit_seen={report['audit_seen']} "
            f"queue_written={report['queue_written']}"
        )
        print(f"phrase={report['phrase']}")
        print(f"message={report['message']}")
        print(f"next_action={report['next_action']}")
    return 0 if report["status"] in {"PASS", "DRY_RUN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
