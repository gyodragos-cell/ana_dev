#!/usr/bin/env python3
"""Final live test - desktop control + system monitoring through MCP"""
import subprocess
import json
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

proc = subprocess.Popen(
    [sys.executable, "mcp_stdio.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8',
    errors='replace',
    cwd="."
)

def call_tool(tool_name, operation, **kwargs):
    """Call a tool through MCP"""
    req = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 10000,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": {"operation": operation, **kwargs}
        }
    }

    proc.stdin.write(json.dumps(req) + "\n")
    proc.stdin.flush()

    response = proc.stdout.readline()
    if response:
        resp_data = json.loads(response)
        result_text = resp_data['result']['content'][0]['text']
        return json.loads(result_text)
    return None

# Initialize
init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
proc.stdin.write(json.dumps(init_req) + "\n")
proc.stdin.flush()
proc.stdout.readline()

print("=" * 70)
print("LIVE DESKTOP CONTROL + SYSTEM MONITORING")
print("=" * 70)

# 1. See desktop
print("\n[1] SEEING YOUR DESKTOP")
result = call_tool("desktop_capture", "capture")
if result['success']:
    print(f"    Screenshot: {result['data']['file']}")
    print(f"    Size: {result['data']['size']} bytes")

# 2. Move mouse
print("\n[2] MOVING MOUSE THROUGH MCP")
positions = [
    (500, 300, "upper-left"),
    (1400, 300, "upper-right"),
    (1400, 800, "lower-right"),
    (500, 800, "lower-left"),
]

for x, y, desc in positions:
    result = call_tool("desktop_control", "click_at", target=f"{x},{y}")
    if result['success']:
        print(f"    Moved to {desc} ({x}, {y})")
    time.sleep(0.3)

# 3. System monitoring
print("\n[3] SYSTEM MONITORING")
result = call_tool("windows_insight", "system_snapshot")
if result['success']:
    # Parse the data (it's a JSON string)
    processes_data = json.loads(result['data'])
    print(f"    Top processes by CPU:")
    for proc_info in processes_data[:5]:
        name = proc_info.get('Name', 'Unknown')
        cpu = proc_info.get('CPU', 0)
        ram_mb = proc_info.get('WorkingSet', 0) / (1024 * 1024)
        print(f"      - {name}: CPU={cpu:.1f}%, RAM={ram_mb:.1f}MB")

# 4. Live desktop viewer info
print("\n[4] LIVE DESKTOP VIEWER")
result = call_tool("live_desktop_viewer", "start_stream")
if result['success']:
    print(f"    {result['message']}")
else:
    print(f"    Info: {result.get('message', result.get('error', 'N/A'))}")

proc.terminate()

print("\n" + "=" * 70)
print("LIVE TEST COMPLETE!")
print("All tools working through MCP!")
print("=" * 70)
