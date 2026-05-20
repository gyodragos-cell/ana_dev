#!/usr/bin/env python3
"""Live desktop control through MCP - simulating Kiro usage"""
import subprocess
import json
import sys
import io
import time

# Set UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Start MCP server
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

def send_request(method, tool_name, arguments):
    """Send MCP request and get response"""
    req = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 10000,
        "method": method,
        "params": {
            "name": tool_name,
            "arguments": arguments
        } if method == "tools/call" else {}
    }
    
    proc.stdin.write(json.dumps(req) + "\n")
    proc.stdin.flush()
    
    response = proc.stdout.readline()
    if response:
        return json.loads(response)
    return None

print("=" * 70)
print("LIVE DESKTOP CONTROL THROUGH MCP")
print("=" * 70)

# Initialize
print("\n1. Initializing MCP connection...")
init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
proc.stdin.write(json.dumps(init_req) + "\n")
proc.stdin.flush()
response = proc.stdout.readline()
print("   Connected!")

# Step 1: See desktop
print("\n2. Taking screenshot to see your desktop...")
resp = send_request("tools/call", "desktop_capture", {"operation": "capture"})
if resp and 'result' in resp:
    result_text = resp['result']['content'][0]['text']
    result_data = json.loads(result_text)
    if result_data['success']:
        print(f"   Screenshot saved: {result_data['data']['file']}")
        print(f"   Size: {result_data['data']['size']} bytes")
        print("   I can see your desktop now!")
    else:
        print(f"   Error: {result_data['error']}")

# Step 2: Move mouse through desktop_control tool
print("\n3. Moving mouse through MCP desktop_control tool...")

moves = [
    (960, 540, "center of screen"),
    (100, 100, "top-left corner"),
    (1820, 1080, "bottom-right corner"),
    (960, 540, "center again"),
]

for x, y, description in moves:
    print(f"\n   Moving to {description} ({x}, {y})...")
    resp = send_request("tools/call", "desktop_control", {
        "operation": "click_at",
        "target": f"{x},{y}"
    })
    
    if resp and 'result' in resp:
        result_text = resp['result']['content'][0]['text']
        result_data = json.loads(result_text)
        if result_data['success']:
            print(f"   SUCCESS: {result_data['message']}")
        else:
            print(f"   ERROR: {result_data['error']}")
    
    time.sleep(0.5)

# Step 3: Check system info with windows_insight_tool
print("\n4. Checking system info with windows_insight_tool...")
resp = send_request("tools/call", "windows_insight", {
    "operation": "get_vitals"
})

if resp and 'result' in resp:
    result_text = resp['result']['content'][0]['text']
    result_data = json.loads(result_text)
    if result_data['success']:
        vitals = result_data['data']
        print(f"   CPU: {vitals.get('cpu_percent', 'N/A')}%")
        print(f"   RAM: {vitals.get('memory_percent', 'N/A')}%")
        print(f"   Processes: {vitals.get('process_count', 'N/A')}")
    else:
        print(f"   ERROR: {result_data['error']}")

# Cleanup
proc.terminate()
try:
    proc.wait(timeout=2)
except:
    proc.kill()

print("\n" + "=" * 70)
print("LIVE TEST COMPLETE!")
print("=" * 70)
