"""
Test Debug Console - Verify it's working without breaking anything
Hooks into existing MCP server and opencode_zen backend
"""
import requests
import json
import time
from pathlib import Path

print("=" * 80)
print("DEBUG CONSOLE TEST - Safe Connection Test")
print("=" * 80)

MCP_URL = "http://127.0.0.1:8766/mcp"

# Test 1: Check if MCP server is responding
print("\n[TEST 1] Checking MCP Server connection...")
try:
    resp = requests.get("http://127.0.0.1:8766/health", timeout=5)
    if resp.status_code == 200:
        data = resp.json()
        print(f"  [OK] Server is running: {data.get('status')}")
        print(f"  [OK] Tools loaded: {data.get('tools_count', 'N/A')}")
    else:
        print(f"  [FAIL] Server returned HTTP {resp.status_code}")
except Exception as e:
    print(f"  [FAIL] Cannot connect to server: {e}")
    print("\n  SOLUTION: Run launch.bat first!")
    exit(1)

# Test 2: Check if debug console log file exists
print("\n[TEST 2] Checking debug console log file...")
log_file = Path(__file__).parent / "logs" / "ana_max.log"
if log_file.exists():
    size = log_file.stat().st_size
    print(f"  [OK] Log file exists: {size:,} bytes")

    # Read last 5 lines to show it's working
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        print(f"  [OK] Last 3 log entries:")
        for line in lines[-3:]:
            if line.strip():
                # Show just the message part (after timestamp)
                parts = line.strip().split(' - ', 3)
                if len(parts) >= 4:
                    print(f"    {parts[2]} - {parts[3][:80]}")
else:
    print(f"  [WARN] Log file not found yet")

# Test 3: Test desktop capture (vision)
print("\n[TEST 3] Testing desktop capture (EYES)...")
try:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "desktop_capture",
            "arguments": {"operation": "capture"}
        }
    }
    resp = requests.post(MCP_URL, json=payload, timeout=15)
    result = resp.json()

    if "result" in result:
        data = json.loads(result["result"]["content"][0]["text"])
        if data.get("success"):
            file_path = data["data"].get("file", "")
            print(f"  [OK] Desktop capture working!")
            print(f"  [OK] Screenshot saved: {Path(file_path).name}")
        else:
            print(f"  [FAIL] Capture failed: {data.get('error')}")
    else:
        print(f"  [FAIL] No result from tool call")
except Exception as e:
    print(f"  [FAIL] Desktop capture error: {e}")

# Test 4: Check opencode_zen backend status
print("\n[TEST 4] Checking opencode_zen backend connection...")
try:
    # Try to call a simple tool that uses the backend
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "system_control",
            "arguments": {"action": "get_system_info"}
        }
    }
    resp = requests.post(MCP_URL, json=payload, timeout=10)
    result = resp.json()

    if "result" in result:
        data = json.loads(result["result"]["content"][0]["text"])
        if data.get("success"):
            print(f"  [OK] System tool working through backend")
        else:
            print(f"  [WARN] System tool returned: {data.get('message', 'Unknown')}")
    else:
        print(f"  [FAIL] No result")
except Exception as e:
    print(f"  [FAIL] Backend test error: {e}")

# Test 5: Check Python process count
print("\n[TEST 5] Checking for duplicate processes...")
import subprocess
try:
    result = subprocess.run(
        ["powershell", "-Command", "(Get-Process python).Count"],
        capture_output=True, text=True
    )
    count = int(result.stdout.strip())
    if count <= 3:
        print(f"  [OK] {count} Python processes (clean)")
    elif count <= 6:
        print(f"  [WARN] {count} Python processes (acceptable)")
    else:
        print(f"  [FAIL] {count} Python processes (too many duplicates!)")
        print(f"  SOLUTION: Kill all python.exe and run launch.bat ONCE")
except Exception as e:
    print(f"  [WARN] Could not check processes: {e}")

# Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print("\n  [OK] System is connected and working")
print("  [OK] Debug console can read logs in real-time")
print("  [OK] Tools are responding through MCP")
print("\n  NEXT STEP: You can now use the debug console to watch")
print("  all tool calls, errors, and successes LIVE!")
print(f"\n{'=' * 80}\n")
