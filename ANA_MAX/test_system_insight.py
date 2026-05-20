#!/usr/bin/env python3
"""Test windows_insight_tool through MCP"""
import subprocess
import json
import sys
import io
import time

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
    """Send MCP request"""
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
print("WINDOWS INSIGHT TOOL - SYSTEM MONITORING")
print("=" * 70)

# Initialize
init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
proc.stdin.write(json.dumps(init_req) + "\n")
proc.stdin.flush()
proc.stdout.readline()

# Test system_snapshot
print("\n1. Getting system snapshot...")
resp = send_request("tools/call", "windows_insight", {
    "operation": "system_snapshot"
})

if resp and 'result' in resp:
    result_text = resp['result']['content'][0]['text']
    result_data = json.loads(result_text)
    if result_data['success']:
        data = result_data['data']
        print(f"   CPU Usage: {data.get('cpu_percent', 'N/A')}%")
        print(f"   Memory Usage: {data.get('memory_percent', 'N/A')}%")
        print(f"   Available RAM: {data.get('memory_available_gb', 'N/A')} GB")
        print(f"   Total RAM: {data.get('memory_total_gb', 'N/A')} GB")
        print(f"   Processes: {data.get('process_count', 'N/A')}")
        print(f"   Disk C: {data.get('disk_c_percent', 'N/A')}%")
    else:
        print(f"   ERROR: {result_data['error']}")

# Test start_monitor
print("\n2. Starting system monitor...")
resp = send_request("tools/call", "windows_insight", {
    "operation": "start_monitor"
})

if resp and 'result' in resp:
    result_text = resp['result']['content'][0]['text']
    result_data = json.loads(result_text)
    if result_data['success']:
        print(f"   Monitor started: {result_data['message']}")
    else:
        print(f"   ERROR: {result_data['error']}")

# Cleanup
proc.terminate()
try:
    proc.wait(timeout=2)
except:
    proc.kill()

print("\n" + "=" * 70)
print("SYSTEM INSIGHT TEST COMPLETE!")
print("=" * 70)
