"""
Vision Check - Takes screenshot after launch to verify everything started correctly
Uses desktop_capture tool via MCP
"""
import requests
import json
from datetime import datetime

print("=" * 80)
print("VISION CHECK - Post-Launch Screenshot Analysis")
print("=" * 80)

# Wait for processes to stabilize
print("\n[VISION] Waiting 5 seconds for processes to stabilize...")
import time
time.sleep(5)

# Take screenshot
print("[VISION] Capturing desktop screenshot...")
try:
    resp = requests.post(
        'http://127.0.0.1:8766/mcp',
        json={
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'tools/call',
            'params': {
                'name': 'desktop_capture',
                'arguments': {
                    'operation': 'capture'
                }
            }
        },
        timeout=10
    )

    data = resp.json()
    content = data['result']['content'][0]['text']
    result = json.loads(content)

    if result['success']:
        screenshot_file = result['data']['file']
        print(f"\nâœ… SCREENSHOT CAPTURED!")
        print(f"   File: {screenshot_file}")
        print(f"   Size: {result['data']['size']} bytes")
        print(f"   Method: {result['data']['method']}")
        print(f"\n   [V] You can now view this screenshot to verify launch state")
    else:
        print(f"\nâŒ SCREENSHOT FAILED: {result.get('error', 'Unknown error')}")

except Exception as e:
    print(f"\n ERROR: {e}")

# Get window list
print("\n[VISION] Getting active window list...")
try:
    resp = requests.post(
        'http://127.0.0.1:8766/mcp',
        json={
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'tools/call',
            'params': {
                'name': 'desktop_capture',
                'arguments': {
                    'operation': 'get_windows'
                }
            }
        },
        timeout=10
    )

    data = resp.json()
    content = data['result']['content'][0]['text']
    result = json.loads(content)

    if result['success']:
        windows = result['data']['windows']
        print(f"\nâœ… Found {len(windows)} active windows:")

        # Filter for ANA MAX related windows
        ana_windows = [w for w in windows if any(keyword in w.get('title', '').lower()
                       for keyword in ['ana', 'mcp', 'voice', 'qoder', 'frida', 'vision'])]

        if ana_windows:
            print(f"\n   ANA MAX related windows:")
            for w in ana_windows[:10]:  # Show first 10
                print(f"     - {w.get('title', 'Untitled')}")
        else:
            print("\n   âš ï¸  No ANA MAX windows detected in window list")
            print("   (Some may be minimized and not shown)")
    else:
        print(f"\nâŒ Window list failed: {result.get('error', 'Unknown error')}")

except Exception as e:
    print(f"\nâŒ ERROR getting windows: {e}")

print(f"\n{'=' * 80}")
print("VISION CHECK COMPLETE")
print(f"{'=' * 80}\n")
print("Press Ctrl+C to exit, or close this window")

# Keep running
try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    pass
