#!/usr/bin/env python3
"""Use tools through MCP and see errors on screen"""
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
        resp_data = json.loads(response)
        result_text = resp_data['result']['content'][0]['text']
        return json.loads(result_text)
    return None

# Initialize
init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
proc.stdin.write(json.dumps(init_req) + "\n")
proc.stdin.flush()
proc.stdout.readline()

print("=" * 70)
print("USING TOOLS TO SEE ERRORS ON YOUR SCREEN")
print("=" * 70)

# Step 1: Take screenshot to see current state
print("\n[STEP 1] Taking screenshot to see VS Code...")
result = call_tool("desktop_capture", "capture")
if result['success']:
    screenshot_file = result['data']['file']
    print(f"Screenshot saved: {screenshot_file}")
    print("I can see your VS Code now!")
else:
    print(f"Error: {result['error']}")

# Step 2: Use windows_uia_bridge to see UI elements
print("\n[STEP 2] Scanning UI elements to find errors...")
result = call_tool("windows_uia_bridge", "scan")
if result['success']:
    ui_data = result['data']
    print(f"Found {ui_data.get('element_count', 0)} UI elements")
    
    # Look for error indicators
    if 'elements' in ui_data:
        elements = ui_data['elements']
        error_elements = [e for e in elements if 'error' in str(e).lower() or 'red' in str(e).lower()]
        if error_elements:
            print(f"Found {len(error_elements)} potential error elements:")
            for elem in error_elements[:5]:
                print(f"  - {elem}")
else:
    print(f"Info: {result.get('message', 'N/A')}")

# Step 3: Use system_control to get system info
print("\n[STEP 3] Checking system status...")
result = call_tool("system_control", "vitals")
if result['success']:
    vitals = result['data']
    print(f"System vitals:")
    print(f"  CPU: {vitals.get('cpu_percent', 'N/A')}%")
    print(f"  Memory: {vitals.get('memory_percent', 'N/A')}%")
    print(f"  Processes: {vitals.get('process_count', 'N/A')}")
else:
    print(f"Error: {result['error']}")

# Step 4: Use frida to see processes
print("\n[STEP 4] Checking running processes with Frida...")
result = call_tool("frida_instrument", "list_processes")
if result['success']:
    processes = result['data'].get('processes', [])
    print(f"Found {result['data'].get('count', 0)} processes")
    
    # Look for VS Code and related processes
    vscode_procs = [p for p in processes if 'code' in p['name'].lower() or 'vscode' in p['name'].lower()]
    if vscode_procs:
        print("VS Code processes:")
        for p in vscode_procs:
            print(f"  - PID {p['pid']}: {p['name']}")
else:
    print(f"Error: {result['error']}")

# Step 5: Use windows_deep_sight for detailed system view
print("\n[STEP 5] Deep system inspection...")
result = call_tool("windows_deep_sight", "processes")
if result['success']:
    data = result['data']
    print(f"System processes: {data.get('count', 'N/A')}")
    if 'processes' in data:
        top_procs = data['processes'][:5]
        print("Top processes:")
        for p in top_procs:
            print(f"  - {p.get('name', 'Unknown')}: {p.get('cpu', 'N/A')}% CPU")
else:
    print(f"Info: {result.get('message', 'N/A')}")

# Step 6: Take another screenshot to see if anything changed
print("\n[STEP 6] Taking final screenshot...")
result = call_tool("desktop_capture", "capture")
if result['success']:
    print(f"Final screenshot: {result['data']['file']}")
    print("Comparison: Check if any errors appeared on screen")
else:
    print(f"Error: {result['error']}")

proc.terminate()

print("\n" + "=" * 70)
print("TOOL USAGE COMPLETE!")
print("Check VS Code for any errors that appeared")
print("=" * 70)
