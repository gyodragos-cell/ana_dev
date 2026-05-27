"""
LIVE DEBUG CONSOLE - Real-time MCP Server Event Monitor
Shows all tool calls, successes, and errors like a game developer console
"""
import time
import sys
from pathlib import Path
from datetime import datetime

LOG_FILE = Path(__file__).parent.parent / "logs" / "ana_max.log"

print("=" * 80)
print("ANA MAX LIVE DEBUG CONSOLE")
print("=" * 80)
print(f"\nMonitoring: {LOG_FILE}")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\n" + "=" * 80)
print("LIVE EVENT STREAM - Watch for errors and tool calls!")
print("=" * 80 + "\n")

# Track last position
last_size = 0

if LOG_FILE.exists():
    last_size = LOG_FILE.stat().st_size
else:
    print("[WARNING] Log file not found yet, waiting...")
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Color codes for Windows
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def format_log_line(line):
    """Format log line with colors based on content"""
    line = line.strip()
    if not line:
        return ""

    # Timestamp
    if "2026-" in line or "2025-" in line:
        timestamp = line[:23]
        rest = line[23:]

        # Color based on log level
        if "ERROR" in rest or "FAIL" in rest.upper():
            return f"{BLUE}{timestamp}{RESET} {RED}{rest}{RESET}"
        elif "WARNING" in rest or "WARN" in rest.upper():
            return f"{BLUE}{timestamp}{RESET} {YELLOW}{rest}{RESET}"
        elif "TOOL CALL" in rest or "tools/call" in rest:
            return f"{BLUE}{timestamp}{RESET} {GREEN}{rest}{RESET}"
        elif "TOOL END" in rest or "success=True" in rest:
            return f"{BLUE}{timestamp}{RESET} {GREEN}[OK] {rest}{RESET}"
        elif "success=False" in rest:
            return f"{BLUE}{timestamp}{RESET} {RED}[FAIL] {rest}{RESET}"
        else:
            return f"{BLUE}{timestamp}{RESET} {rest}"

    return line

# Main monitoring loop
print("Waiting for events...\n")

try:
    while True:
        if LOG_FILE.exists():
            current_size = LOG_FILE.stat().st_size

            if current_size > last_size:
                # New content available
                with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(last_size)
                    new_lines = f.readlines()
                    last_size = current_size

                for line in new_lines:
                    formatted = format_log_line(line)
                    if formatted:
                        print(formatted)

        time.sleep(0.5)  # Check every 500ms

except KeyboardInterrupt:
    print(f"\n\n{'=' * 80}")
    print("DEBUG CONSOLE STOPPED")
    print(f"{'=' * 80}\n")
    sys.exit(0)
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
