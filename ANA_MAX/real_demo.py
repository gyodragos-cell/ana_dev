#!/usr/bin/env python3
import subprocess, json, sys, io, time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

proc = subprocess.Popen([sys.executable, 'mcp_stdio.py'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', cwd='.')

def tool(name, op, **kw):
    req = {'jsonrpc': '2.0', 'id': int(time.time()*1000)%10000, 'method': 'tools/call', 'params': {'name': name, 'arguments': {'operation': op, **kw}}}
    proc.stdin.write(json.dumps(req) + '\n')
    proc.stdin.flush()
    r = proc.stdout.readline()
    if r:
        try:
            return json.loads(json.loads(r)['result']['content'][0]['text'])
        except:
            return None
    return None

# Init
init = {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {}}
proc.stdin.write(json.dumps(init) + '\n')
proc.stdin.flush()
proc.stdout.readline()

print('REAL DEMO - MUTA MOUSEUL PE ECRAN')
print('=' * 70)

# 1. Screenshot INAINTE
print('\n[INAINTE] Screenshot 1 - Văd desktop-ul...')
r = tool('desktop_capture', 'capture')
if r and r.get('success'):
    file1 = r['data']['file']
    print(f'    Screenshot salvat: {file1}')

time.sleep(1)

# 2. Muta mouseul - REAL
print('\n[MUTA] Mișc mouseul pe ecran...')
positions = [
    (100, 100, 'top-left'),
    (1800, 100, 'top-right'),
    (1800, 1000, 'bottom-right'),
    (100, 1000, 'bottom-left'),
    (960, 540, 'center'),
]

for x, y, desc in positions:
    r = tool('desktop_control', 'click_at', target=f'{x},{y}')
    if r and r.get('success'):
        print(f'    ✓ Mouseul la {desc} ({x}, {y})')
    time.sleep(0.5)

time.sleep(1)

# 3. Screenshot DUPA
print('\n[DUPA] Screenshot 2 - Verific poziția finală...')
r = tool('desktop_capture', 'capture')
if r and r.get('success'):
    file2 = r['data']['file']
    print(f'    Screenshot salvat: {file2}')

print('\n' + '=' * 70)
print('COMPARA CELE 2 SCREENSHOT-URI:')
print(f'  INAINTE: {file1}')
print(f'  DUPA:    {file2}')
print('\nDaca mouseul s-a miscat, o sa vezi diferenta in screenshot-uri!')
print('=' * 70)

proc.terminate()
