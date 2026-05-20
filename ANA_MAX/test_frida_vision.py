#!/usr/bin/env python3
"""Test Frida tool to see processes on desktop"""
import sys
sys.path.insert(0, '.')

from tools.frida_automation import FridaTool

# Create Frida tool
frida = FridaTool()

print("=" * 60)
print("🔍 FRIDA VISION TEST - Seeing Your Desktop Processes")
print("=" * 60)

# Test 1: Check Frida version
print("\n1️⃣  Checking Frida version...")
result = frida.execute(operation="version")
if result.is_success:
    print(f"   ✅ Frida version: {result.data.get('version')}")
else:
    print(f"   ❌ Error: {result.error}")

# Test 2: List processes
print("\n2️⃣  Listing running processes...")
result = frida.execute(operation="list_processes")
if result.is_success:
    processes = result.data.get('processes', [])
    print(f"   ✅ Found {result.data.get('count')} processes")
    print("\n   Top 15 processes:")
    for proc in processes[:15]:
        print(f"      PID {proc['pid']:>6} - {proc['name']}")
else:
    print(f"   ❌ Error: {result.error}")

# Test 3: List devices
print("\n3️⃣  Checking Frida devices...")
result = frida.execute(operation="devices")
if result.is_success:
    devices = result.data.get('devices', [])
    print(f"   ✅ Found {result.data.get('count')} devices")
    for device in devices:
        print(f"      - {device}")
else:
    print(f"   ⚠️  Info: {result.error}")

print("\n" + "=" * 60)
print("✨ Frida Vision Test Complete!")
print("=" * 60)
