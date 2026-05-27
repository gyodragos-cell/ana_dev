"""
ANA MAX Comprehensive Smoke Test
Tests all critical components before admin launch
"""
import requests
import json
import sys
from pathlib import Path

print("=" * 80)
print("ANA MAX SMOKE TEST - Pre-Admin Launch Verification")
print("=" * 80)

MCP_URL = "http://127.0.0.1:8766/mcp"
results = {"passed": 0, "failed": 0, "warnings": 0}

def test(name, func):
    """Run a test and track results"""
    try:
        result = func()
        if result.get("success"):
            print(f"  [PASS] {name}")
            results["passed"] += 1
        elif result.get("warning"):
            print(f"  [WARN] {name}: {result.get('message', '')}")
            results["warnings"] += 1
        else:
            print(f"  [FAIL] {name}: {result.get('error', 'Unknown error')}")
            results["failed"] += 1
    except Exception as e:
        print(f"  [FAIL] {name}: {str(e)}")
        results["failed"] += 1

def call_mcp(method, params=None):
    """Make MCP request"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {}
    }
    resp = requests.post(MCP_URL, json=payload, timeout=10)
    return resp.json()

def call_tool(name, args):
    """Call a tool via MCP"""
    resp = call_mcp("tools/call", {"name": name, "arguments": args})
    if "result" in resp:
        return json.loads(resp["result"]["content"][0]["text"])
    return {"success": False, "error": resp.get("error", "No result")}

# Test 1: MCP Server Connection
print("\n[1/10] Testing MCP Server connection...")
def test_mcp_connection():
    try:
        resp = requests.get("http://127.0.0.1:8766/health", timeout=5)
        if resp.status_code == 200:
            return {"success": True, "message": f"Server healthy: {resp.json().get('status')}"}
        return {"success": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

test("MCP Server Connection", test_mcp_connection)

# Test 2: Tools List
print("\n[2/10] Testing tools list...")
def test_tools_list():
    resp = call_mcp("tools/list")
    tools = resp.get("result", {}).get("tools", [])
    if len(tools) >= 50:
        return {"success": True, "message": f"{len(tools)} tools loaded"}
    return {"success": False, "error": f"Only {len(tools)} tools loaded (expected 50+)"}

test("Tools List", test_tools_list)

# Test 3: Desktop Capture (Vision)
print("\n[3/10] Testing Desktop Vision...")
def test_desktop_capture():
    result = call_tool("desktop_capture", {"operation": "capture"})
    if result.get("success"):
        file = result["data"].get("file", "")
        return {"success": True, "message": f"Screenshot saved: {Path(file).name}"}
    return {"success": False, "error": result.get("error", "Capture failed")}

test("Desktop Capture", test_desktop_capture)

# Test 4: File Operations
print("\n[4/10] Testing File Operations...")
def test_file_operations():
    test_file = Path(__file__).parent / "test_smoke_temp.txt"
    test_file.write_text("Smoke test data")

    result = call_tool("file_operations", {
        "operation": "read",
        "path": str(test_file)
    })

    test_file.unlink(missing_ok=True)

    if result.get("success"):
        return {"success": True, "message": "File read/write OK"}
    return {"success": False, "error": result.get("error", "File ops failed")}

test("File Operations", test_file_operations)

# Test 5: Voice System
print("\n[5/10] Testing Voice System...")
def test_voice():
    result = call_tool("edge_tts_voice", {
        "operation": "speak",
        "text": "Smoke test voice check",
        "async": "false"
    })
    if result.get("success"):
        return {"success": True, "message": "Voice system operational"}
    return {"warning": True, "message": result.get("message", "Voice may not be working")}

test("Voice System", test_voice)

# Test 6: FRIDA Instrument
print("\n[6/10] Testing FRIDA...")
def test_frida():
    result = call_tool("frida_instrument", {
        "operation": "version",
        "confirm": True
    })
    if result.get("success"):
        return {"success": True, "message": f"FRIDA version: {result.get('data', 'N/A')}"}
    return {"warning": True, "message": "FRIDA requires admin privileges"}

test("FRIDA Instrument", test_frida)

# Test 7: System Info
print("\n[7/10] Testing System Info...")
def test_system_info():
    result = call_tool("system_control", {"action": "get_system_info"})
    if result.get("success"):
        data = result.get("data", {})
        return {"success": True, "message": f"OS: {data.get('os', 'N/A')}, Machine: {data.get('machine', 'N/A')}"}
    return {"success": False, "error": result.get("error", "System info failed")}

test("System Info", test_system_info)

# Test 8: Windows List
print("\n[8/10] Testing Windows Detection...")
def test_windows_list():
    result = call_tool("desktop_capture", {"operation": "get_windows"})
    if result.get("success"):
        windows = result.get("data", {}).get("windows", [])
        return {"success": True, "message": f"{len(windows)} windows detected"}
    return {"success": False, "error": result.get("error", "Window list failed")}

test("Windows Detection", test_windows_list)

# Test 9: Process Count
print("\n[9/10] Checking Python Process Count...")
def test_process_count():
    import subprocess
    result = subprocess.run(
        ["powershell", "-Command", "(Get-Process python).Count"],
        capture_output=True, text=True
    )
    count = int(result.stdout.strip())
    if count <= 5:
        return {"success": True, "message": f"{count} Python processes (OK)"}
    return {"warning": True, "message": f"{count} Python processes (may have duplicates)"}

test("Process Count", test_process_count)

# Test 10: Log File
print("\n[10/10] Checking Log Files...")
def test_logs():
    log_file = Path(__file__).parent / "logs" / "ana_max.log"
    if log_file.exists():
        size = log_file.stat().st_size
        return {"success": True, "message": f"Log file exists ({size:,} bytes)"}
    return {"warning": True, "message": "Log file not found yet"}

test("Log Files", test_logs)

# Summary
print("\n" + "=" * 80)
print("SMOKE TEST RESULTS")
print("=" * 80)
print(f"\n  PASSED:   {results['passed']}")
print(f"  WARNINGS: {results['warnings']}")
print(f"  FAILED:   {results['failed']}")
print(f"  TOTAL:    {results['passed'] + results['warnings'] + results['failed']}")

if results['failed'] == 0:
    print("\n  [OK] All critical tests passed! Safe to run as admin.")
elif results['failed'] <= 2:
    print("\n  [WARN] Some tests failed, but system may still work.")
else:
    print("\n  [FAIL] Too many failures! Fix issues before running as admin.")

print(f"\n{'=' * 80}\n")

# Exit code
sys.exit(0 if results['failed'] == 0 else 1)
