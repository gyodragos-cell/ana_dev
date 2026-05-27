#!/usr/bin/env python3
"""Test calling Frida tool through MCP"""
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

print("=" * 60)
print("TESTING FRIDA THROUGH MCP")
print("=" * 60)

# Send initialize
init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
proc.stdin.write(json.dumps(init_req) + "\n")
proc.stdin.flush()
response = proc.stdout.readline()
print("\n1. Initialize: OK")

# Send tools/list
list_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
proc.stdin.write(json.dumps(list_req) + "\n")
proc.stdin.flush()
response = proc.stdout.readline()
resp_data = json.loads(response)
tools_count = len(resp_data.get('result', {}).get('tools', []))
print(f"2. tools/list: {tools_count} tools found")

# Find frida_instrument tool
frida_tool = None
for tool in resp_data['result']['tools']:
    if 'frida' in tool['name'].lower():
        frida_tool = tool
        break

if frida_tool:
    print(f"\n3. Found Frida tool: {frida_tool['name']}")
    print(f"    Description: {frida_tool['description'][:60]}...")
    print(f"    Parameters: {list(frida_tool['inputSchema']['properties'].keys())}")

    # Call frida_instrument with list_processes operation
    call_req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": frida_tool['name'],
            "arguments": {
                "operation": "list_processes"
            }
        }
    }

    print(f"\n4. Calling {frida_tool['name']} with operation=list_processes...")
    proc.stdin.write(json.dumps(call_req) + "\n")
    proc.stdin.flush()
    response = proc.stdout.readline()
    resp_data = json.loads(response)

    if 'result' in resp_data:
        result_text = resp_data['result']['content'][0]['text']
        result_data = json.loads(result_text)

        if result_data['success']:
            processes = result_data['data'].get('processes', [])
            print(f"    SUCCESS: Found {result_data['data'].get('count')} processes")
            print(f"    Top 5 processes:")
            for proc_info in processes[:5]:
                print(f"      - PID {proc_info['pid']:>6}: {proc_info['name']}")
        else:
            print(f"    ERROR: {result_data['error']}")
    else:
        print(f"    ERROR in response: {resp_data}")
else:
    print("ERROR: Frida tool not found!")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)

# Cleanup
proc.terminate()
proc.wait(timeout=2)
