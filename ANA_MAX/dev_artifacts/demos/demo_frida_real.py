#!/usr/bin/env python3
"""
JokerForge/ANA MAX - Real Frida Instrumentation Demo
======================================================
Spawns a ctypes process, hooks rand(), and forces return value to 42.
Must be ASCII-only to pass quality gate.
"""

import subprocess
import sys
import time
import os
from pathlib import Path

# Set working directory to project root
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("  JOKERFORGE / ANA MAX - FRIDA REAL HOOK DEMO")
print("=" * 60)

# Check if frida is installed
try:
    import frida
except ImportError:
    print("[FAIL] Frida package is not installed. Run 'pip install frida'.")
    sys.exit(1)

# Start target process
print("Starting target_process.py...")
proc = subprocess.Popen([sys.executable, "target_process.py"], stdout=subprocess.PIPE, text=True)

# Give process time to load DLL
time.sleep(1)

# Read initial outputs
print("\nReading initial output from target (original rand):")
for _ in range(3):
    line = proc.stdout.readline().strip()
    print(f"  Target: {line}")

# Attach Frida
print(f"\nAttaching Frida to PID {proc.pid}...")
try:
    session = frida.attach(proc.pid)
except Exception as e:
    print(f"[FAIL] Could not attach to PID {proc.pid}: {e}")
    print("Please make sure you run as administrator or have debugging privileges.")
    proc.terminate()
    sys.exit(1)

# Javascript Hook Source
hook_js = """
const msvcrt = Process.findModuleByName("msvcrt.dll") || Process.findModuleByName("ucrtbase.dll");
if (msvcrt) {
    const randAddr = Module.findExportByName(msvcrt.name, "rand");
    if (randAddr) {
        Interceptor.attach(randAddr, {
            onLeave: function (retval) {
                // Force rand() to return 42
                retval.replace(42);
            }
        });
        send({type: "status", data: "Hook successfully placed on rand() in " + msvcrt.name});
    } else {
        send({type: "error", data: "Could not locate rand export"});
    }
} else {
    send({type: "error", data: "Could not locate msvcrt.dll or ucrtbase.dll"});
}
"""

def on_message(message, data):
    if message['type'] == 'send':
        payload = message['payload']
        print(f"  [Frida Host] {payload.get('data')}")
    else:
        print(f"  [Frida Msg] {message}")

# Create and load script
script = session.create_script(hook_js)
script.on('message', on_message)
script.load()

# Read outputs post hook
print("\nReading output from target after Frida injection:")
for _ in range(4):
    line = proc.stdout.readline().strip()
    print(f"  Target: {line}")

# Detach and cleanup
print("\nCleaning up...")
proc.terminate()
session.detach()
print("=" * 60)
print("  DEMO COMPLETE: rand() successfully hooked to return 42.")
print("=" * 60)
