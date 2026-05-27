"""
ANA MAX - Desktop Vision Diagnostic

Run this from a normal double-clicked .bat window to check whether the current
Windows session allows screenshots and visible window enumeration.
"""

from __future__ import annotations

import getpass
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
REPORT_FILE = BASE_DIR / "desktop_vision_diag_report.txt"
SHOT_DIR = BASE_DIR / "screenshots"


def line(text: str = "") -> str:
    print(text)
    return text


def run_command(command: list[str]) -> tuple[int, str, str]:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as exc:
        return 1, "", str(exc)


def image_stats(path: Path) -> str:
    try:
        from PIL import Image, ImageStat

        with Image.open(path) as img:
            rgb = img.convert("RGB")
            stat = ImageStat.Stat(rgb)
            extrema = rgb.getextrema()
            mean = [round(value, 2) for value in stat.mean]
            max_channel = max(high for _, high in extrema)
            return (
                f"{path.name}: size={rgb.width}x{rgb.height}, bytes={path.stat().st_size}, "
                f"mean={mean}, max_channel={max_channel}"
            )
    except Exception as exc:
        return f"{path.name}: image stats failed: {exc}"


def test_screenshot_methods() -> list[str]:
    SHOT_DIR.mkdir(exist_ok=True)
    results: list[str] = []

    try:
        import mss

        path = SHOT_DIR / "diag_user_mss.png"
        with mss.mss() as sct:
            sct.shot(output=str(path))
        results.append("mss OK - " + image_stats(path))
    except Exception as exc:
        results.append(f"mss FAIL - {exc}")

    try:
        from PIL import ImageGrab

        path = SHOT_DIR / "diag_user_pil.png"
        ImageGrab.grab().save(path)
        results.append("PIL OK - " + image_stats(path))
    except Exception as exc:
        results.append(f"PIL FAIL - {exc}")

    try:
        from PIL import ImageGrab

        path = SHOT_DIR / "diag_user_pil_all.png"
        ImageGrab.grab(all_screens=True).save(path)
        results.append("PIL all_screens OK - " + image_stats(path))
    except Exception as exc:
        results.append(f"PIL all_screens FAIL - {exc}")

    try:
        import pyautogui

        path = SHOT_DIR / "diag_user_pyautogui.png"
        pyautogui.screenshot(str(path))
        results.append("pyautogui OK - " + image_stats(path))
    except Exception as exc:
        results.append(f"pyautogui FAIL - {exc}")

    return results


def main() -> int:
    lines: list[str] = []
    lines.append(line("=" * 70))
    lines.append(line("ANA MAX - DESKTOP VISION DIAGNOSTIC"))
    lines.append(line("=" * 70))
    lines.append(line(f"time: {datetime.now().isoformat(timespec='seconds')}"))
    lines.append(line(f"python: {sys.executable}"))
    lines.append(line(f"user getpass: {getpass.getuser()}"))
    lines.append(line(f"env USERNAME: {os.environ.get('USERNAME')}"))
    lines.append(line(f"env SESSIONNAME: {os.environ.get('SESSIONNAME')}"))

    code, stdout, stderr = run_command(["whoami"])
    lines.append(line(f"whoami: {stdout or stderr}"))

    code, stdout, stderr = run_command(["query", "session"])
    lines.append(line(""))
    lines.append(line("query session:"))
    lines.append(line(stdout or stderr))

    code, stdout, stderr = run_command([
        "powershell",
        "-NoProfile",
        "-Command",
        "Get-Process | Where-Object { $_.MainWindowTitle } | "
        "Select-Object -First 20 Id,ProcessName,MainWindowTitle | Format-Table -AutoSize | Out-String",
    ])
    lines.append(line(""))
    lines.append(line("visible windows:"))
    lines.append(line(stdout or stderr or "<none>"))

    lines.append(line(""))
    lines.append(line("screenshot methods:"))
    for result in test_screenshot_methods():
        lines.append(line(result))

    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    line("")
    line(f"Report saved: {REPORT_FILE}")
    line("Press Enter to close.")
    try:
        input()
    except EOFError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
