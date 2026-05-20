#!/usr/bin/env python3
"""Simple MCP test without emoji"""
import subprocess
import json
import sys
import time

# Start mcp_stdio.py
proc = subprocess.Popen(
    [sys.executable, "mcp_stdio.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    cwd="."
)

print("TEST: MCP Frida Call")
print("=" * 50)

# Initialize
init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
proc.stdin.write(json.dumps(init_req) + "\n")
proc.stdin.flush()
response = proc.stdout.readline()
print("1. Initialize: OK")

# List tools
list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
proc.stdin.write(json.dumps(list_req) + "\n")
proc.stdin.flush()
response = proc.stdout.readline()
resp_data = json.loads(response)
tools_count = len(resp_data.get('result', {}).get('tools', []))
print(f"2. tools/list: {tools_count} tools")

# Call Frida
call_req = {
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": "frida_instrument",
        "arguments": {"operation": "list_processes"}
    }
}

print("3. Calling frida_instrument...")
proc.stdin.write(json.dumps(call_req) + "\n")
proc.stdin.flush()

# Wait for response with timeout
start = time.time()
response = None
while time.time() - start < 10:
    try:
        response = proc.stdout.readline()
        if response:
            break
    except:
        pass
    time.sleep(0.1)

if response:
    print("   Response received!")
    resp_data = json.loads(response)
    result_text = resp_data['result']['content'][0]['text']
    result_data = json.loads(result_text)
    
    if result_data['success']:
        count = result_data['data'].get('count')
        print(f"   SUCCESS: Found {count} processes")
    else:
        print(f"   ERROR: {result_data['error']}")
else:
    print("   TIMEOUT: No response received")

# Cleanup
proc.terminate()
try:
    proc.wait(timeout=2)
except:
    proc.kill()

print("=" * 50)
print("Test complete")
