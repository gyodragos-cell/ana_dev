"""Use Frida to see what's running under the hood"""
import requests
import json

# Call Frida tool through MCP
resp = requests.post('http://127.0.0.1:8766/mcp', json={
    'jsonrpc': '2.0',
    'id': 12,
    'method': 'tools/call',
    'params': {
        'name': 'frida_instrument',
        'arguments': {'operation': 'list_processes'}
    }
})

data = resp.json()
result_text = data['result']['content'][0]['text']
result = json.loads(result_text)

processes = result.get('data', {}).get('processes', [])

print(f"\n{'='*70}")
print(f"FRIDA UNDER-THE-HOOD VIEW: {len(processes)} processes detected")
print(f"{'='*70}\n")

# Show ANA-related processes
ana_processes = [p for p in processes if 'python' in p['name'].lower() or 'cmd' in p['name'].lower()]
print(f"Python/CMD processes: {len(ana_processes)}\n")

for p in ana_processes[:15]:
    print(f"  PID {p['pid']:>6}: {p['name']}")

print(f"\n{'='*70}")
print("This is what's running UNDER THE HOOD!")
print(f"{'='*70}\n")
