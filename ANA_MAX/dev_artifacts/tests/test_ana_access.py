import sys
import json
sys.path.insert(0, '.')

from tools.qoder_ana_integration import ANAToolClient

print("=" * 60)
print("  ANA MAX Tools - Full Access Test")
print("=" * 60)

ana = ANAToolClient()

# Test 1: System Info
print("\n[1/5] Testing System Control...")
try:
    result = ana.call_tool('system_control', action='get_system_info')
    data = json.loads(result['content'][0]['text'])
    print(f"âœ… OS: {data.get('os', 'N/A')}")
    print(f"âœ… Python: {data.get('python_version', 'N/A')}")
    print(f"âœ… Machine: {data.get('machine', 'N/A')}")
except Exception as e:
    print(f"âŒ System Control Error: {e}")

# Test 2: Desktop Capture (EYES!)
print("\n[2/5] Testing Desktop Capture (EYES)...")
try:
    result = ana.call_tool('desktop_capture')
    data = json.loads(result['content'][0]['text'])
    print(f"âœ… Screenshot captured: {data.get('status', 'OK')}")
    if 'image_path' in data:
        print(f"âœ… Saved to: {data['image_path']}")
except Exception as e:
    print(f"âŒ Desktop Capture Error: {e}")

# Test 3: File Operations
print("\n[3/5] Testing File Operations...")
try:
    result = ana.call_tool('file_operations', action='list', path='c:\\Users\\billy\\Desktop')
    data = json.loads(result['content'][0]['text'])
    print(f"âœ… Desktop files listed: {len(data.get('files', []))} items")
except Exception as e:
    print(f"âŒ File Operations Error: {e}")

# Test 4: Terminal Access
print("\n[4/5] Testing Terminal Access...")
try:
    result = ana.call_tool('terminal', command='echo Terminal Access Working')
    data = json.loads(result['content'][0]['text'])
    print(f"âœ… Terminal working: {data.get('output', 'OK')}")
except Exception as e:
    print(f"âŒ Terminal Error: {e}")

# Test 5: List All Available Tools
print("\n[5/5] Listing All Available Tools...")
try:
    tools = ana.list_tools()
    print(f"âœ… Total tools available: {len(tools)}")
    print("\nðŸ“‹ Available Tools:")
    for i, tool in enumerate(tools[:10], 1):
        print(f"   {i}. {tool}")
    if len(tools) > 10:
        print(f"   ... and {len(tools) - 10} more")
except Exception as e:
    print(f"âŒ List Tools Error: {e}")

print("\n" + "=" * 60)
print("  Test Complete!")
print("=" * 60)
