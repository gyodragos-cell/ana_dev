#!/usr/bin/env python3
"""Test calling file_operations tool through MCP"""
import subprocess
import json
import sys
import io

# Set UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Start mcp_stdio.py
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

print("TEST: MCP file_operations Call")
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

# Call file_operations to list a directory
call_req = {
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": "file_operations",
        "arguments": {
            "operation": "list",
            "path": "."
        }
    }
}

print("3. Calling file_operations...")
proc.stdin.write(json.dumps(call_req) + "\n")
proc.stdin.flush()

# Read response
response = proc.stdout.readline()
if response:
    print("   Response received!")
    resp_data = json.loads(response)
    result_text = resp_data['result']['content'][0]['text']
    result_data = json.loads(result_text)
    
    if result_data['success']:
        print(f"   SUCCESS: {result_data['message']}")
    else:
        print(f"   ERROR: {result_data['error']}")
else:
    print("   TIMEOUT: No response")

# Cleanup
proc.terminate()
try:
    proc.wait(timeout=2)
except:
    proc.kill()

print("=" * 50)
