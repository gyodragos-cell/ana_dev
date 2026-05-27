"""Use FRIDA tool properly through MCP to see all processes"""
import requests
import json

print("=" * 80)
print("FRIDA - UNDER THE HOOD PROCESS ANALYSIS")
print("=" * 80)

# Call Frida tool with confirmation
resp = requests.post('http://127.0.0.1:8766/mcp', json={
    'jsonrpc': '2.0',
    'id': 100,
    'method': 'tools/call',
    'params': {
        'name': 'frida_instrument',
        'arguments': {'operation': 'list_processes'},
        'confirm': True
    }
})

data = resp.json()
result_text = data['result']['content'][0]['text']
result = json.loads(result_text)

if result.get('success'):
    processes = result['data']['processes']
    print(f"\n Total processes found: {len(processes)}\n")

    # Filter ANA-related processes
    ana_processes = [p for p in processes if any(x in p['name'].lower() for x in ['python', 'cmd', 'qoder', 'node'])]

    print(f" ANA/Qoder related processes: {len(ana_processes)}\n")
    for p in ana_processes[:20]:
        print(f"   PID {p['pid']:>6}: {p['name']:<20} | {p.get('command', 'N/A')[:60]}")

    print(f"\n{'=' * 80}")
else:
    print(f"\n Error: {result.get('message', 'Unknown error')}")
    print(f"{'=' * 80}")
