"""Test Frida tool capabilities"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

print("="*70)
print("FRIDA TOOL TEST")
print("="*70)

from tools.frida_automation import FridaTool

tool = FridaTool()

# Test 1: List processes
print("\n[TEST 1] List Processes...")
result = tool.execute(operation='list_processes')
print(f"  Status: {'SUCCESS' if result.is_success else 'FAILED'}")
if result.is_success:
    print(f"  Message: {result.message}")
    processes = result.data.get('processes', []) if result.data else []
    print(f"  Found {len(processes)} processes")
    # Show first 5 processes
    for p in processes[:5]:
        print(f"    - PID {p.get('pid')}: {p.get('name')}")
else:
    print(f"  Error: {result.error}")

# Test 2: Get Frida version
print("\n[TEST 2] Frida Version...")
try:
    import frida
    print(f"  Frida version: {frida.__version__}")
    print(f"  OK: Frida is installed and working!")
except Exception as e:
    print(f"  ERROR: Frida error: {e}")

# Test 3: Attach to a process (Dolphin Anty if running)
print("\n[TEST 3] Try to attach to Dolphin Anty...")
result = tool.execute(operation='list_processes')
if result.is_success and result.data:
    processes = result.data.get('processes', [])
    dolphin = [p for p in processes if 'dolphin' in p.get('name', '').lower() or 'anty' in p.get('name', '').lower()]
    if dolphin:
        pid = dolphin[0].get('pid')
        print(f"  Found Dolphin Anty: PID {pid}")
        # Use 'target' parameter, not 'pid'
        attach_result = tool.execute(operation='attach', target=pid)
        print(f"  Attach status: {'SUCCESS' if attach_result.is_success else 'FAILED'}")
        if attach_result.is_success:
            print(f"  OK: Successfully attached to PID {pid}!")
        else:
            print(f"  Error: {attach_result.error}")
    else:
        print("  SKIP: Dolphin Anty not found in processes")

print("\n" + "="*70)
print("FRIDA TEST COMPLETE")
print("="*70)
