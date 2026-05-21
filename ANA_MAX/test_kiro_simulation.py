#!/usr/bin/env python3
"""Simulate what Kiro does when connecting to MCP server"""
import subprocess
import json
import sys
import io
import time

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

print("SIMULATING KIRO MCP CONNECTION")
print("=" * 60)

# Step 1: Initialize
print("\n1. Sending initialize request...")
init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
proc.stdin.write(json.dumps(init_req) + "\n")
proc.stdin.flush()

response = proc.stdout.readline()
resp_data = json.loads(response)

print(f"   Protocol: {resp_data['result']['protocolVersion']}")
print(f"   Server: {resp_data['result']['serverInfo']['name']}")
print(f"   Capabilities: {resp_data['result']['capabilities']}")

# Check if tools capability is present
has_tools = 'tools' in resp_data['result']['capabilities']
tools_listchanged = resp_data['result']['capabilities'].get('tools', {}).get('listChanged', False)

print(f"\n   Has 'tools' capability: {has_tools}")
print(f"   'tools.listChanged': {tools_listchanged}")

if not tools_listchanged:
    print("   WARNING: Kiro might not list tools!")

# Step 2: List tools
print("\n2. Sending tools/list request...")
list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
proc.stdin.write(json.dumps(list_req) + "\n")
proc.stdin.flush()

response = proc.stdout.readline()
resp_data = json.loads(response)

tools = resp_data.get('result', {}).get('tools', [])
print(f"   Found {len(tools)} tools")

if len(tools) > 0:
    print("\n   First 5 tools:")
    for tool in tools[:5]:
        params_count = len(tool['inputSchema']['properties'])
        print(f"      - {tool['name']} ({params_count} params)")
    print(f"\n   SUCCESS: Kiro should see all {len(tools)} tools!")
else:
    print("   ERROR: No tools returned!")

# Cleanup
proc.terminate()
try:
    proc.wait(timeout=2)
except Exception as e:
    proc.kill()

print("\n" + "=" * 60)
print("Simulation complete")
