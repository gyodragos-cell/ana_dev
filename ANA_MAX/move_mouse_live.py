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

print('MUTAND MOUSEUL IN TIMP REAL')
print('=' * 70)

# Move 1
print('\nMuta mouseul la (500, 500)...')
r = tool('desktop_control', 'click_at', target='500,500')
if r and r.get('success'):
    print(f'✓ {r["message"]}')
time.sleep(1)

# Move 2
print('\nMuta mouseul la (1000, 500)...')
r = tool('desktop_control', 'click_at', target='1000,500')
if r and r.get('success'):
    print(f'✓ {r["message"]}')
time.sleep(1)

# Move 3
print('\nMuta mouseul la (500, 1000)...')
r = tool('desktop_control', 'click_at', target='500,1000')
if r and r.get('success'):
    print(f'✓ {r["message"]}')

print('\n' + '=' * 70)
print('GATA! Mouseul mutat la toate 3 pozitii!')
print('=' * 70)

proc.terminate()
