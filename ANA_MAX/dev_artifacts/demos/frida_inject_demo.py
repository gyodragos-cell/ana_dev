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

print('FRIDA INJECTION DEMO')
print('=' * 70)

# 1. List processes
print('\n[1] Listez procesele care ruleaza...')
r = tool('frida_instrument', 'list_processes')
if r and r.get('success'):
    processes = r['data']['processes']
    print(f'    Gasite {r["data"]["count"]} procese')

    # Find explorer.exe
    explorer_pid = None
    for p in processes:
        if 'explorer' in p['name'].lower():
            explorer_pid = p['pid']
            print(f'    âœ“ Gasit explorer.exe (PID {explorer_pid})')
            break

    if not explorer_pid:
        print('    ! explorer.exe nu gasit, folosesc alt proces')
        explorer_pid = processes[0]['pid']
        print(f'    âœ“ Folosesc {processes[0]["name"]} (PID {explorer_pid})')

# 2. Generate hook script
print('\n[2] Generez script de hook...')
r = tool('frida_instrument', 'hook', target=str(explorer_pid), module='kernel32.dll', pattern='CreateProcess')
if r and r.get('success'):
    script = r['data']['script']
    print(f'    âœ“ Script generat pentru a intercepta CreateProcess')
    print(f'    Script length: {len(script)} caractere')

# 3. List modules
print('\n[3] Listez modulele din proces...')
r = tool('frida_instrument', 'list_modules', target=str(explorer_pid))
if r and r.get('success'):
    modules = r['data']['modules']
    print(f'    âœ“ Gasite {r["data"]["count"]} module')
    for m in modules[:5]:
        print(f'      - {m["name"]}')

# 4. Find functions
print('\n[4] Caut functii in kernel32.dll...')
r = tool('frida_instrument', 'find_functions', target=str(explorer_pid), module='kernel32.dll', pattern='Create')
if r and r.get('success'):
    functions = r['data']['functions']
    print(f'    âœ“ Gasite {r["data"]["count"]} functii cu "Create"')
    for f in functions[:5]:
        print(f'      - {f["name"]} @ {f["address"]}')
else:
    print(f'    Info: {r}')

print('\n' + '=' * 70)
print('âœ¨ FRIDA INJECTION DEMO COMPLETE!')
print('=' * 70)

proc.terminate()
