#!/usr/bin/env python3
"""Test Frida tool through MCP"""
import subprocess
import json
import sys

# Start mcp_stdio.py
proc = subprocess.Popen(
    [sys.executable, "mcp_stdio.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    cwd="."
)

# Initialize
init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
proc.stdin.write(json.dumps(init_req) + "\n")
proc.stdin.flush()
proc.stdout.readline()  # Skip response

# Call Frida tool to list processes
frida_req = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "frida_instrument",
        "arguments": {
            "operation": "list_processes"
        }
    }
}
proc.stdin.write(json.dumps(frida_req) + "\n")
proc.stdin.flush()

# Read response
response = proc.stdout.readline()
resp_data = json.loads(response)

print("Frida Tool Response:")
print(json.dumps(resp_data, indent=2))

# Cleanup
proc.terminate()
proc.wait(timeout=2)
