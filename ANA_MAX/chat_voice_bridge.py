"""
ANA MAX - Chat Voice Bridge

Speaks text copied from chat and lines appended to a local voice queue.
This gives Codex/ANA a practical local bridge without needing access to the
chat application's private internals.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

from tools.live_voice_bridge import speak


BASE_DIR = Path(__file__).resolve().parent
QUEUE_FILE = BASE_DIR / "voice_queue.txt"


def get_clipboard_text() -> str:
    """Read Windows clipboard text without adding Python dependencies."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
            capture_output=True,
            text=True,
            timeout=3,
        )
    except Exception:
        return ""

    if result.returncode != 0:
        return ""
    return normalize_text(result.stdout)


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def should_speak(text: str, max_chars: int) -> bool:
    if not text:
        return False
    if len(text) > max_chars:
        return False
    lowered = text.lower()
    secret_words = ("api key", "password", "token", "secret", "private key")
    return not any(word in lowered for word in secret_words)


def speak_queue(last_pos: int, max_chars: int) -> int:
    QUEUE_FILE.touch(exist_ok=True)
    with QUEUE_FILE.open("r", encoding="utf-8", errors="replace") as handle:
        handle.seek(last_pos)
        new_text = normalize_text(handle.read())
        last_pos = handle.tell()

    if should_speak(new_text, max_chars):
        speak(new_text)
    return last_pos


def main() -> int:
    parser = argparse.ArgumentParser(description="Speak copied chat text and ANA queue messages.")
    parser.add_argument("--poll", type=float, default=1.0, help="Clipboard polling interval in seconds.")
    parser.add_argument("--max-chars", type=int, default=900, help="Skip copied text longer than this.")
    parser.add_argument("--no-clipboard", action="store_true", help="Only read voice_queue.txt.")
    args = parser.parse_args()

    QUEUE_FILE.touch(exist_ok=True)
    last_clipboard = ""
    last_queue_pos = QUEUE_FILE.stat().st_size

    print("=" * 70)
    print("ANA MAX - CHAT VOICE BRIDGE")
    print("=" * 70)
    print("Copy any chat text and ANA will speak it.")
    print(f"Queue file: {QUEUE_FILE}")
    print("Secrets are skipped if they contain words like token/password/api key.")
    print("Press Ctrl+C to stop.")
    print("=" * 70)
    speak("ANA chat voice bridge is active.")

    try:
        while True:
            last_queue_pos = speak_queue(last_queue_pos, args.max_chars)

            if not args.no_clipboard:
                text = get_clipboard_text()
                if text != last_clipboard and should_speak(text, args.max_chars):
                    last_clipboard = text
                    speak(text)

            time.sleep(args.poll)
    except KeyboardInterrupt:
        speak("ANA chat voice bridge stopped.")
        print("\nStopped.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
