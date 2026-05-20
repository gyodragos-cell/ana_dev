#!/usr/bin/env python3
"""Test Desktop Capture to see your screen"""
import sys
sys.path.insert(0, '.')

from tools.desktop_capture import DesktopCaptureTool

# Create Desktop Capture tool
capture = DesktopCaptureTool()

print("=" * 60)
print("📸 DESKTOP CAPTURE TEST - Seeing Your Screen")
print("=" * 60)

# Test: Capture desktop
print("\n1️⃣  Capturing desktop screenshot...")
result = capture.execute(operation="capture", region=None)

if result.is_success:
    data = result.data
    print(f"   ✅ Screenshot captured!")
    print(f"      Resolution: {data.get('width')} x {data.get('height')} pixels")
    print(f"      File: {data.get('file')}")
    print(f"      Size: {data.get('size')} bytes")
    print(f"      Format: {data.get('format')}")
    print(f"\n   📍 Screenshot saved to: {data.get('file')}")
else:
    print(f"   ❌ Error: {result.error}")

print("\n" + "=" * 60)
print("✨ Desktop Capture Test Complete!")
print("=" * 60)
