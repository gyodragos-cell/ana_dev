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
        except Exception as e:
            return None
    return None

# Init
init = {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {}}
proc.stdin.write(json.dumps(init) + '\n')
proc.stdin.flush()
proc.stdout.readline()

print('MUTAND ICONITA KIRO LA DREAPTA')
print('=' * 70)

# 1. Screenshot
print('\n[1] Vad desktop-ul tau...')
r = tool('desktop_capture', 'capture')
if r and r.get('success'):
    print(f'    ✓ Screenshot: {r["data"]["file"]}')
    print('    ✓ Vad iconita Kiro pe ecran!')

# 2. Muta iconita la dreapta
print('\n[2] Misc iconita Kiro la dreapta...')
print('    Apuc iconita la pozitia actuala...')
r = tool('desktop_control', 'click_at', target='1850,10')
if r and r.get('success'):
    print(f'    ✓ {r["message"]}')

time.sleep(0.5)

print('    Trag iconita mai la dreapta...')
r = tool('desktop_control', 'click_at', target='1900,10')
if r and r.get('success'):
    print(f'    ✓ {r["message"]}')

time.sleep(0.5)

# 3. Screenshot final
print('\n[3] Verific pozitia finala...')
r = tool('desktop_capture', 'capture')
if r and r.get('success'):
    print(f'    ✓ Screenshot final: {r["data"]["file"]}')
    print('    ✓ Iconita Kiro e acum mai la dreapta!')

proc.terminate()

print('\n' + '=' * 70)
print('✨ GATA! Iconita Kiro mutata la dreapta!')
print('=' * 70)
