"""ANA MAX local voice inbox.

One-shot microphone dictation for the private lab. The script uses Windows
System.Speech when available, stores only compact text records, and can copy the
recognized text to the clipboard for pasting into Codex.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
if str(ANA_ROOT) not in sys.path:
    sys.path.insert(0, str(ANA_ROOT))

from tools.conversation_audit import append_conversation_audit

MEMORY_DIR = ANA_ROOT / "memory"
INBOX_JSONL = MEMORY_DIR / "voice_inbox.jsonl"
LATEST_TXT = MEMORY_DIR / "voice_inbox_latest.txt"
STATUS_TXT = MEMORY_DIR / "voice_inbox_status.txt"

SECRET_WORDS = ("api key", "password", "token", "secret", "private key")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_text(text: str) -> str:
    text = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]
    return " ".join(line for line in lines if line).strip()


def contains_secret_words(text: str) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in SECRET_WORDS)


def powershell_json(script: str, timeout: int) -> dict[str, Any]:
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    output = (result.stdout or "").strip()
    if result.returncode != 0:
        return {
            "success": False,
            "error": (result.stderr or output or f"powershell exited {result.returncode}").strip(),
        }
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        return {"success": False, "error": "non-json powershell output", "output": output[:500]}
    return parsed if isinstance(parsed, dict) else {"success": False, "error": "unexpected powershell output"}


def recognize_once(duration: int, language: str = "") -> dict[str, Any]:
    duration = max(2, min(int(duration), 30))
    culture_line = ""
    if language:
        escaped_language = language.replace("'", "''")
        culture_line = (
            f"$culture = [System.Globalization.CultureInfo]::GetCultureInfo('{escaped_language}'); "
            "$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine($culture); "
        )
    else:
        culture_line = "$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine; "

    script = (
        "$ErrorActionPreference = 'Stop'; "
        "Add-Type -AssemblyName System.Speech; "
        + culture_line +
        "$recognizer.SetInputToDefaultAudioDevice(); "
        "$grammar = New-Object System.Speech.Recognition.DictationGrammar; "
        "$recognizer.LoadGrammar($grammar); "
        f"$result = $recognizer.Recognize([TimeSpan]::FromSeconds({duration})); "
        "if ($null -eq $result) { "
        "  $payload = @{ success = $false; error = 'no speech recognized' }; "
        "} else { "
        "  $payload = @{ success = $true; text = $result.Text; confidence = $result.Confidence }; "
        "} "
        "$recognizer.Dispose(); "
        "$payload | ConvertTo-Json -Compress"
    )
    return powershell_json(script, timeout=duration + 10)


def copy_to_clipboard(text: str) -> bool:
    if not text:
        return False
    script = "$input | Set-Clipboard"
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        input=text,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=5,
    )
    return result.returncode == 0


def foreground_title() -> str:
    script = (
        "Add-Type @'\n"
        "using System;\n"
        "using System.Runtime.InteropServices;\n"
        "using System.Text;\n"
        "public class Win32 {\n"
        "  [DllImport(\"user32.dll\")] public static extern IntPtr GetForegroundWindow();\n"
        "  [DllImport(\"user32.dll\", SetLastError=true, CharSet=CharSet.Auto)] "
        "public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);\n"
        "}\n"
        "'@; "
        "$b = New-Object System.Text.StringBuilder 512; "
        "$h = [Win32]::GetForegroundWindow(); "
        "[void][Win32]::GetWindowText($h, $b, $b.Capacity); "
        "$b.ToString()"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=5,
    )
    return normalize_text(result.stdout) if result.returncode == 0 else ""


def strip_submit_prefix(text: str, prefixes: list[str]) -> tuple[bool, str]:
    normalized = normalize_text(text)
    lowered = normalized.lower()
    for prefix in prefixes:
        cleaned = prefix.strip().lower()
        if not cleaned:
            continue
        candidates = (cleaned, f"{cleaned} ", f"{cleaned}:")
        if any(lowered.startswith(candidate) for candidate in candidates):
            body = normalized[len(cleaned):].lstrip(" :,-")
            return True, body or normalized
    return False, normalized


def title_allowed(title: str, allowed_fragments: list[str]) -> bool:
    lowered = title.lower()
    return any(fragment.strip().lower() in lowered for fragment in allowed_fragments if fragment.strip())


def send_to_focused_window(text: str, *, press_enter: bool, allowed_titles: list[str]) -> dict[str, Any]:
    title = foreground_title()
    if not title_allowed(title, allowed_titles):
        return {"success": False, "reason": "foreground_window_not_allowed", "title": title}
    if not copy_to_clipboard(text):
        return {"success": False, "reason": "clipboard_failed", "title": title}
    script = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "[System.Windows.Forms.SendKeys]::SendWait('^v'); "
    )
    if press_enter:
        script += "[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')"
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=5,
    )
    return {
        "success": result.returncode == 0,
        "reason": "" if result.returncode == 0 else (result.stderr or "sendkeys_failed").strip(),
        "title": title,
    }


def build_record(
    text: str,
    *,
    confidence: float | None,
    source: str,
    copied: bool,
    submitted: bool = False,
    submit_title: str = "",
) -> dict[str, Any]:
    normalized = normalize_text(text)
    sensitive = contains_secret_words(normalized)
    stored_text = "" if sensitive else normalized
    return {
        "schema": "ana.voice_inbox.entry.v1",
        "ts": now_iso(),
        "source": source,
        "success": bool(stored_text),
        "text": stored_text,
        "confidence": confidence,
        "copied_to_clipboard": copied,
        "submitted_to_focused_window": submitted,
        "submit_title": submit_title,
        "sensitive_skipped": sensitive,
    }


def save_record(record: dict[str, Any]) -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    with INBOX_JSONL.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    LATEST_TXT.write_text(record.get("text", ""), encoding="utf-8")
    append_conversation_audit(
        "voice_inbox",
        str(record.get("text") or ""),
        copied=bool(record.get("copied_to_clipboard")),
        submitted=bool(record.get("submitted_to_focused_window")),
        sensitive_skipped=bool(record.get("sensitive_skipped")),
        metadata={
            "voice_source": record.get("source"),
            "confidence": record.get("confidence"),
            "sensitive_skipped": record.get("sensitive_skipped"),
        },
    )


def save_status(text: str) -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    STATUS_TXT.write_text(text, encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.mock_text:
        raw = {"success": True, "text": args.mock_text, "confidence": 1.0}
        source = "mock"
    else:
        raw = recognize_once(args.duration, args.language)
        source = "system_speech"

    if not raw.get("success"):
        return {
            "schema": "ana.voice_inbox.v1",
            "success": False,
            "message": raw.get("error") or "No speech recognized.",
            "error": raw.get("error") or "No speech recognized.",
            "data": {"source": source},
        }

    text = normalize_text(str(raw.get("text") or ""))
    safe_text = text and not contains_secret_words(text)
    copied = copy_to_clipboard(text) if args.copy and safe_text else False
    submit = {"success": False, "title": ""}
    if args.auto_submit and safe_text:
        should_submit, submit_text = strip_submit_prefix(text, args.submit_prefix)
        if should_submit:
            submit = send_to_focused_window(
                submit_text,
                press_enter=args.press_enter,
                allowed_titles=args.allowed_title,
            )
    record = build_record(
        text,
        confidence=raw.get("confidence"),
        source=source,
        copied=copied,
        submitted=bool(submit.get("success")),
        submit_title=str(submit.get("title") or ""),
    )
    if not args.no_write:
        save_record(record)

    message = "Voice inbox captured text."
    if record["sensitive_skipped"]:
        message = "Voice inbox skipped sensitive text."
    elif copied:
        message = "Voice inbox captured text and copied it to clipboard."
    if submit.get("success"):
        message = "Voice inbox captured text and submitted it to the focused window."
    return {
        "schema": "ana.voice_inbox.v1",
        "success": bool(record["text"]),
        "message": message,
        "error": None if record["text"] else "empty or sensitive text",
        "data": {
            "record": record,
            "latest": str(LATEST_TXT),
            "jsonl": str(INBOX_JSONL),
        },
    }


def run_continuous(args: argparse.Namespace) -> int:
    save_status("starting")
    print(
        json.dumps(
            {
                "schema": "ana.voice_inbox.daemon.v1",
                "status": "starting",
                "duration": args.duration,
                "auto_submit": args.auto_submit,
                "submit_prefix": args.submit_prefix,
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    last_text = ""
    save_status("running")
    while True:
        payload = run(args)
        record = payload.get("data", {}).get("record", {})
        text = str(record.get("text") or "")
        if payload.get("success") and text and text != last_text:
            last_text = text
            print(json.dumps(payload, ensure_ascii=False), flush=True)
        elif args.verbose:
            print(json.dumps(payload, ensure_ascii=False), flush=True)
        time.sleep(max(0.2, float(args.pause)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Capture one microphone dictation into ANA voice inbox.")
    parser.add_argument("--duration", type=int, default=8, help="Listening duration in seconds, 2-30.")
    parser.add_argument("--language", default="", help="Optional recognizer culture, for example en-US.")
    parser.add_argument("--copy", action="store_true", help="Copy recognized text to the clipboard.")
    parser.add_argument("--continuous", action="store_true", help="Keep listening in repeated one-shot windows.")
    parser.add_argument("--pause", type=float, default=0.3, help="Pause between continuous listens.")
    parser.add_argument("--auto-submit", action="store_true", help="Paste recognized text into the focused allowed window.")
    parser.add_argument("--press-enter", action="store_true", help="Press Enter after auto-submit paste.")
    parser.add_argument(
        "--submit-prefix",
        action="append",
        default=["codex", "ana"],
        help="Only auto-submit when recognized text starts with this word. Repeatable.",
    )
    parser.add_argument(
        "--allowed-title",
        action="append",
        default=["Visual Studio Code", "Code", "Codex", "ChatGPT"],
        help="Allowed foreground window title fragment for auto-submit. Repeatable.",
    )
    parser.add_argument("--verbose", action="store_true", help="Print failed continuous recognition attempts too.")
    parser.add_argument("--no-write", action="store_true", help="Do not write memory files.")
    parser.add_argument("--mock-text", default="", help="Test path that bypasses microphone recognition.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.continuous:
        return run_continuous(args)
    payload = run(args)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
