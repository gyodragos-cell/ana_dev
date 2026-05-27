from frida_monitor_live import get_python_processes

procs = get_python_processes()
print(f'\nFRIDA found {len(procs)} Python processes')
for p in procs[:10]:
    print(f'  PID {p["pid"]}: {p["name"]}')
