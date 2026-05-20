#!/usr/bin/env python3
"""Debug windows_insight_tool"""
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

# Initialize
init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
proc.stdin.write(json.dumps(init_req) + "\n")
proc.stdin.flush()
proc.stdout.readline()

# Call system_snapshot
req = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "windows_insight",
        "arguments": {"operation": "system_snapshot"}
    }
}

proc.stdin.write(json.dumps(req) + "\n")
proc.stdin.flush()

response = proc.stdout.readline()
print("Raw response:")
print(response[:500])

resp_data = json.loads(response)
result_text = resp_data['result']['content'][0]['text']
print("\nResult text:")
print(result_text[:500])

result_data = json.loads(result_text)
print("\nParsed result:")
print(f"Success: {result_data['success']}")
print(f"Data type: {type(result_data['data'])}")
print(f"Data: {result_data['data']}")

proc.terminate()
