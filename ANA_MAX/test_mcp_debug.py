#!/usr/bin/env python3
"""Debug MCP response"""
import subprocess
import json
import sys
import io

# Set UTF-8 for this script too
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Start mcp_stdio.py with UTF-8
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

# Initialize
init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
proc.stdin.write(json.dumps(init_req) + "\n")
proc.stdin.flush()
response = proc.stdout.readline()
print("Initialize response OK")

# List tools
list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
proc.stdin.write(json.dumps(list_req) + "\n")
proc.stdin.flush()
response = proc.stdout.readline()
print("tools/list response OK")

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

print("\nCalling frida_instrument...")
proc.stdin.write(json.dumps(call_req) + "\n")
proc.stdin.flush()

# Read response line by line
print("\nResponse lines:")
for i in range(5):
    line = proc.stdout.readline()
    if not line:
        print(f"  Line {i}: (empty)")
        break
    print(f"  Line {i}: {line[:100]}...")

# Cleanup
proc.terminate()
proc.wait(timeout=2)
