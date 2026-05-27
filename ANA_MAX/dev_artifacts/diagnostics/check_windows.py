import requests
import json

resp = requests.post('http://127.0.0.1:8766/mcp', json={
    'jsonrpc': '2.0',
    'id': 1,
    'method': 'tools/call',
    'params': {
        'name': 'desktop_capture',
        'arguments': {'operation': 'get_windows'}
    }
})

data = json.loads(resp.json()['result']['content'][0]['text'])
windows = data.get('data', {}).get('windows', [])

print(f"\nTotal windows: {len(windows)}\n")
print("ANA MAX related windows:")
for w in windows:
    title = w.get('title', 'Untitled')
    if any(k in title.lower() for k in ['ana', 'mcp', 'voice', 'frida', 'python', 'cmd', 'qoder']):
        print(f"  - {title[:100]}")
