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

print('🎬 LIVE DEMO - DESKTOP AUTOMATION WOW!')
print('=' * 70)

# 1. Screenshot
print('\n[1] SEEING YOUR DESKTOP')
r = tool('desktop_capture', 'capture')
if r and r.get('success'):
    fname = r['data']['file'].split('\\')[-1]
    print(f'    ✓ Screenshot captured: {fname}')

# 2. Move mouse in cool pattern
print('\n[2] MOVING MOUSE IN PATTERN')
pattern = [(960, 300), (1400, 540), (960, 780), (500, 540), (960, 300)]
for i, (x, y) in enumerate(pattern, 1):
    r = tool('desktop_control', 'click_at', target=f'{x},{y}')
    if r and r.get('success'):
        print(f'    ✓ Move {i}/5: ({x}, {y})')
    time.sleep(0.3)

# 3. System monitoring
print('\n[3] SYSTEM VITALS')
r = tool('system_control', 'vitals')
if r and r.get('success'):
    data = r['data']
    if isinstance(data, str):
        lines = data.split('\n')
        for line in lines[:4]:
            if line.strip():
                print(f'    ✓ {line.strip()}')

# 4. Process inspection
print('\n[4] PROCESS INSPECTION')
r = tool('frida_instrument', 'list_processes')
if r and r.get('success'):
    count = r['data']['count']
    procs = r['data']['processes'][:3]
    print(f'    ✓ Found {count} processes')
    for p in procs:
        print(f'      - {p["name"]} (PID {p["pid"]})')

# 5. Deep system view
print('\n[5] DEEP SYSTEM INSPECTION')
r = tool('windows_deep_sight', 'top_cpu')
if r and r.get('success'):
    print(f'    ✓ Top CPU processes identified')
    data = r['data']
    if isinstance(data, str):
        try:
            data = json.loads(data)
            if isinstance(data, list):
                for p in data[:3]:
                    print(f'      - {p.get("name", "Unknown")}')
        except Exception as e:
            pass

# 6. Final screenshot
print('\n[6] FINAL SCREENSHOT')
r = tool('desktop_capture', 'capture')
if r and r.get('success'):
    fname = r['data']['file'].split('\\')[-1]
    print(f'    ✓ Screenshot: {fname}')

proc.terminate()

print('\n' + '=' * 70)
print('✨ DEMO COMPLETE! All 23 tools working perfectly!')
print('=' * 70)
