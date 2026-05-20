#!/usr/bin/env python3
"""Test MCP stdio communication"""
import subprocess
import json
import sys

# Start mcp_stdio.py as subprocess
proc = subprocess.Popen(
    [sys.executable, "mcp_stdio.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    cwd="."
)

# Send initialize request
init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
proc.stdin.write(json.dumps(init_req) + "\n")
proc.stdin.flush()

# Read response
response = proc.stdout.readline()
print("Initialize response:", response.strip())

# Send tools/list request
list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
proc.stdin.write(json.dumps(list_req) + "\n")
proc.stdin.flush()

# Read response
response = proc.stdout.readline()
resp_data = json.loads(response)
tools_count = len(resp_data.get('result', {}).get('tools', []))
print(f"\ntools/list response: {tools_count} tools found")

if tools_count > 0:
    print("\nFirst 3 tools:")
    for tool in resp_data['result']['tools'][:3]:
        print(f"  - {tool['name']}")

# Cleanup
proc.terminate()
proc.wait(timeout=2)
