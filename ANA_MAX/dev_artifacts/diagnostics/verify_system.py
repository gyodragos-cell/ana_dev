import requests
import json
import time

print("=" * 80)
print("ANA MAX SYSTEM VERIFICATION - LIVE DEBUG")
print("=" * 80)

# 1. Check MCP Server
print("\n[1] Testing MCP Server connection...")
try:
    r = requests.post('http://127.0.0.1:8766/mcp', json={
        'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'
    }, timeout=5)
    tools = r.json()['result']['tools']
    print(f"    âœ… MCP Server: RUNNING")
    print(f"    âœ… Tools loaded: {len(tools)}")
except Exception as e:
    print(f"    âŒ MCP Server: FAILED - {e}")

# 2. Check FRIDA
print("\n[2] Testing FRIDA connection...")
try:
    r = requests.post('http://127.0.0.1:8766/mcp', json={
        'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
        'params': {'name': 'frida_instrument', 'arguments': {'operation': 'version', 'confirm': True}}
    }, timeout=5)
    result = json.loads(r.json()['result']['content'][0]['text'])
    if result.get('success'):
        print(f"    âœ… FRIDA: CONNECTED")
        print(f"    Version: {result['data']}")
    else:
        print(f"    âš ï¸  FRIDA: {result.get('message', 'Unknown')}")
except Exception as e:
    print(f"    âŒ FRIDA: FAILED - {e}")

# 3. Check Desktop Vision
print("\n[3] Testing Desktop Vision...")
try:
    r = requests.post('http://127.0.0.1:8766/mcp', json={
        'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
        'params': {'name': 'desktop_capture', 'arguments': {'operation': 'capture'}}
    }, timeout=10)
    result = json.loads(r.json()['result']['content'][0]['text'])
    if result.get('success'):
        print(f"    âœ… Desktop Vision: WORKING")
        print(f"    Screenshot: {result['data']['file'].split('\\\\')[-1]}")
    else:
        print(f"    âŒ Desktop Vision: {result.get('error')}")
except Exception as e:
    print(f"    âŒ Desktop Vision: FAILED - {e}")

# 4. Check Voice
print("\n[4] Testing Voice system...")
try:
    r = requests.post('http://127.0.0.1:8766/mcp', json={
        'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
        'params': {'name': 'edge_tts_voice', 'arguments': {'operation': 'speak', 'text': 'System verification complete', 'async': 'false'}}
    }, timeout=10)
    result = json.loads(r.json()['result']['content'][0]['text'])
    if result.get('success'):
        print(f"    âœ… Voice: WORKING")
    else:
        print(f"    âš ï¸  Voice: {result.get('message', result.get('error'))}")
except Exception as e:
    print(f"    âŒ Voice: FAILED - {e}")

# 5. Process count
print("\n[5] Python processes running...")
import subprocess
result = subprocess.run(['powershell', '-Command', '(Get-Process python).Count'],
                       capture_output=True, text=True)
count = int(result.stdout.strip())
print(f"    {'âœ…' if count <= 3 else 'âŒ'} Python processes: {count}")
if count > 3:
    print(f"    âš ï¸  WARNING: Too many processes! Expected 2-3")

print(f"\n{'=' * 80}")
print("VERIFICATION COMPLETE")
print(f"{'=' * 80}\n")
