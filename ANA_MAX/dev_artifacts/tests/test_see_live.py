#!/usr/bin/env python3
"""Live tool usage - see what's on screen"""
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

def call_tool(tool_name, operation, **kwargs):
    """Call a tool through MCP"""
    req = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 10000,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": {"operation": operation, **kwargs}
        }
    }

    proc.stdin.write(json.dumps(req) + "\n")
    proc.stdin.flush()

    response = proc.stdout.readline()
    if response:
        try:
            resp_data = json.loads(response)
            result_text = resp_data['result']['content'][0]['text']
            return json.loads(result_text)
        except Exception as e:
            return None
    return None

# Initialize
init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
proc.stdin.write(json.dumps(init_req) + "\n")
proc.stdin.flush()
proc.stdout.readline()

print("=" * 70)
print("LIVE TOOL USAGE - SEEING YOUR SCREEN")
print("=" * 70)

# 1. Screenshot
print("\n[1] TAKING SCREENSHOT")
result = call_tool("desktop_capture", "capture")
if result and result.get('success'):
    print(f"    Screenshot: {result['data']['file']}")
    print(f"    Size: {result['data']['size']} bytes")
    print("    I can see your VS Code screen now!")
else:
    print(f"    Error: {result}")

# 2. Frida - list processes
print("\n[2] LISTING PROCESSES WITH FRIDA")
result = call_tool("frida_instrument", "list_processes")
if result and result.get('success'):
    count = result['data'].get('count', 0)
    processes = result['data'].get('processes', [])
    print(f"    Found {count} processes")

    # Show VS Code and Kiro
    for p in processes:
        if 'code' in p['name'].lower() or 'kiro' in p['name'].lower():
            print(f"      - {p['name']} (PID {p['pid']})")
else:
    print(f"    Error: {result}")

# 3. System control - vitals
print("\n[3] SYSTEM VITALS")
result = call_tool("system_control", "vitals")
if result and result.get('success'):
    data = result['data']
    # Handle both dict and string
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception as e:
            pass

    if isinstance(data, dict):
        print(f"    CPU: {data.get('cpu_percent', 'N/A')}%")
        print(f"    Memory: {data.get('memory_percent', 'N/A')}%")
        print(f"    Processes: {data.get('process_count', 'N/A')}")
    else:
        print(f"    Data: {str(data)[:100]}")
else:
    print(f"    Error: {result}")

# 4. Windows Deep Sight
print("\n[4] DEEP SYSTEM INSPECTION")
result = call_tool("windows_deep_sight", "processes")
if result and result.get('success'):
    data = result['data']
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception as e:
            pass

    if isinstance(data, dict):
        print(f"    Process count: {data.get('count', 'N/A')}")
        if 'processes' in data:
            for p in data['processes'][:3]:
                print(f"      - {p.get('name', 'Unknown')}")
    else:
        print(f"    Data: {str(data)[:100]}")
else:
    print(f"    Error: {result}")

# 5. Another screenshot
print("\n[5] FINAL SCREENSHOT")
result = call_tool("desktop_capture", "capture")
if result and result.get('success'):
    print(f"    Screenshot: {result['data']['file']}")
    print("    Done! Check if any errors appeared on your screen")
else:
    print(f"    Error: {result}")

proc.terminate()

print("\n" + "=" * 70)
print("TOOL USAGE COMPLETE!")
print("=" * 70)
