import requests
import json

resp = requests.post('http://127.0.0.1:8766/mcp', json={
    'jsonrpc': '2.0',
    'id': 1,
    'method': 'tools/call',
    'params': {
        'name': 'frida_instrument',
        'arguments': {
            'operation': 'list_processes',
            'confirm': True
        }
    }
})

data = json.loads(resp.json()['result']['content'][0]['text'])
py_procs = [p for p in data['data']['processes'] if 'python' in p['name'].lower()]

print(f'\nFRIDA sees {len(py_procs)} Python processes:')
for p in py_procs[:10]:
    print(f'  PID {p["pid"]}: {p["name"]}')
