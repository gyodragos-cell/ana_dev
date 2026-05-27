"""
FRIDA Live Process Monitor - Watches for new processes during launch
Automatically logs all Python processes and detects duplicates
"""
import requests
import json
import time
from datetime import datetime

def get_python_processes():
    """Get list of Python processes via FRIDA"""
    try:
        resp = requests.post(
            'http://127.0.0.1:8766/mcp',
            json={
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'tools/call',
                'params': {
                    'name': 'frida_instrument',
                    'arguments': {
                        'operation': 'list_processes',
                        'confirm': True
                    }
                }
            },
            timeout=5
        )
        data = resp.json()
        content = data['result']['content'][0]['text']
        result = json.loads(content)

        # Filter Python processes
        py_processes = [p for p in result['data']['processes']
                       if 'python' in p['name'].lower()]
        return py_processes
    except Exception as e:
        print(f"[ERROR] FRIDA call failed: {e}")
        return []

print("=" * 80)
print("FRIDA LIVE PROCESS MONITOR")
print("=" * 80)
print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("Watching for new Python processes...\n")

# Take initial snapshot
print("[SNAPSHOT 1] Processes at startup:")
initial_processes = get_python_processes()
print(f"  Found {len(initial_processes)} Python processes")
for p in initial_processes:
    print(f"    PID {p['pid']:>6}: {p['name']}")

print("\n" + "-" * 80)
print("[MONITORING] Waiting for new processes to spawn...\n")

# Monitor for changes
last_count = len(initial_processes)
check_interval = 2  # Check every 2 seconds

while True:
    try:
        time.sleep(check_interval)
        current_processes = get_python_processes()
        current_count = len(current_processes)

        if current_count != last_count:
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"\n[{timestamp}]  CHANGE DETECTED!")
            print(f"  Before: {last_count} processes")
            print(f"  After:  {current_count} processes")

            # Find new processes
            old_pids = {p['pid'] for p in initial_processes}
            new_pids = {p['pid'] for p in current_processes}
            added = new_pids - old_pids
            removed = old_pids - new_pids

            if added:
                print(f"\n  âž• NEW PROCESSES:")
                for pid in added:
                    proc = next(p for p in current_processes if p['pid'] == pid)
                    print(f"     PID {pid}: {proc['name']}")

            if removed:
                print(f"\n  âž– REMOVED PROCESSES:")
                for pid in removed:
                    print(f"     PID {pid}")

            # Update snapshot
            initial_processes = current_processes
            last_count = current_count

            # Check for problems
            if current_count > 3:
                print(f"\n  âŒ WARNING: Too many processes ({current_count})!")
                print(f"     Expected: 2 (MCP Server + Voice)")
                print(f"     Problem: launch.bat may have been run multiple times")
            elif current_count == 2:
                print(f"\n  âœ… PERFECT: Exactly 2 processes running")

            print(f"\n{'-' * 80}\n")

    except KeyboardInterrupt:
        print("\n\n[MONITOR] Stopped by user")
        break
    except Exception as e:
        print(f"\n[ERROR] Monitor error: {e}")
        time.sleep(5)
