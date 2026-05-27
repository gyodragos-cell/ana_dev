#!/usr/bin/env python3
"""Test Frida tool directly"""
import sys
sys.path.insert(0, '.')

from tools.frida_automation import FridaTool

print("Testing Frida tool directly...")
f = FridaTool()

print("Calling list_processes...")
r = f.execute(operation='list_processes')

print(f"Success: {r.is_success}")
print(f"Count: {r.data.get('count') if r.is_success else 'N/A'}")
print(f"Message: {r.message}")

if r.is_success:
    processes = r.data.get('processes', [])
    print(f"\nFirst 5 processes:")
    for p in processes[:5]:
        print(f"  - {p['pid']}: {p['name']}")
