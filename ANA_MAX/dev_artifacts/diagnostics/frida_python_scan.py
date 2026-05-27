import requests
import json

# Get process list from FRIDA
resp = requests.post(
    'http://127.0.0.1:8766/mcp',
    json={
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
    },
    timeout=10
)

data = resp.json()
content = data['result']['content'][0]['text']
result = json.loads(content)

# Filter Python processes
py_processes = [p for p in result['data']['processes'] if 'python' in p['name'].lower()]

print(f"\n{'='*80}")
print(f"FRIDA PROCESS ANALYSIS - Python Processes")
print(f"{'='*80}")
print(f"\nTotal Python processes running: {len(py_processes)}\n")

for p in py_processes:
    print(f"  PID {p['pid']:>6}: {p['name']}")

print(f"\n{'='*80}")

# Check for duplicates
if len(py_processes) > 3:
    print(f"\nâš ï¸  WARNING: Too many Python processes!")
    print(f"   Expected: 2 (MCP Server + Voice Toggle)")
    print(f"   Found: {len(py_processes)}")
    print(f"\n   This means launch.bat was run multiple times!")
else:
    print(f"\nâœ… OK: Normal number of Python processes")

print(f"{'='*80}\n")
