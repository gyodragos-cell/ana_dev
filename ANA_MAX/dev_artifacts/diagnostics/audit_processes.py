import subprocess
import json

# Get all Python processes with details
result = subprocess.run(
    ['powershell', '-Command',
     'Get-Process python | Select-Object Id, ProcessName, Path | ConvertTo-Json'],
    capture_output=True,
    text=True
)

processes = json.loads(result.stdout)

print(f"\n{'='*80}")
print(f"ANA MAX PROCESS AUDIT")
print(f"{'='*80}\n")
print(f"Total Python processes: {len(processes)}\n")

# Group by path
by_path = {}
for p in processes:
    path = p.get('Path', 'unknown')
    if path not in by_path:
        by_path[path] = []
    by_path[path].append(p['Id'])

print("Processes by location:")
for path, pids in by_path.items():
    print(f"\n  {path}")
    print(f"    PIDs: {', '.join(str(pid) for pid in pids)}")
    print(f"    Count: {len(pids)}")

print(f"\n{'='*80}")

# Check for duplicates
expected = 2  # MCP Server + Voice Toggle
actual = len(processes)

if actual > expected:
    print(f"\nâŒ PROBLEM FOUND!")
    print(f"   Expected: {expected} processes (MCP Server + Voice)")
    print(f"   Found: {actual} processes")
    print(f"   Duplicates: {actual - expected}")
    print(f"\n   CAUSE: launch.bat was clicked multiple times!")
    print(f"   FIX: Kill all Python processes and run launch_clean.bat ONCE")
else:
    print(f"\nâœ… Normal: {actual} processes running")

print(f"\n{'='*80}\n")
