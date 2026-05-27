#!/usr/bin/env python3
"""See desktop and move mouse"""
import sys
sys.path.insert(0, '.')

from tools.desktop_capture import DesktopCaptureTool
from tools.desktop_control_tool import DesktopControlTool

print("=" * 70)
print("STEP 1: SEEING YOUR DESKTOP")
print("=" * 70)

# Capture desktop
capture = DesktopCaptureTool()
result = capture.execute(operation="capture", region=None)

if result.is_success:
    data = result.data
    print(f"\nâœ“ Screenshot captured!")
    print(f"  File: {data.get('file')}")
    print(f"  Size: {data.get('size')} bytes")
    print(f"\n  I can see your desktop now!")
else:
    print(f"âœ— Error: {result.error}")

print("\n" + "=" * 70)
print("STEP 2: MOVING YOUR MOUSE")
print("=" * 70)

# Move mouse to center of screen
desktop_control = DesktopControlTool()

print("\nMoving mouse to center of screen (960, 540)...")
result = desktop_control.execute(
    operation="move_mouse",
    x=960,
    y=540
)

if result.is_success:
    print(f"âœ“ Mouse moved!")
    print(f"  Message: {result.message}")
else:
    print(f"âœ— Error: {result.error}")

print("\nWaiting 1 second...")
import time
time.sleep(1)

print("\nMoving mouse to top-left (100, 100)...")
result = desktop_control.execute(
    operation="move_mouse",
    x=100,
    y=100
)

if result.is_success:
    print(f"âœ“ Mouse moved!")
else:
    print(f"âœ— Error: {result.error}")

print("\nWaiting 1 second...")
time.sleep(1)

print("\nMoving mouse to bottom-right (1820, 1080)...")
result = desktop_control.execute(
    operation="move_mouse",
    x=1820,
    y=1080
)

if result.is_success:
    print(f"âœ“ Mouse moved!")
else:
    print(f"âœ— Error: {result.error}")

print("\n" + "=" * 70)
print("DONE! Did you see the mouse move?")
print("=" * 70)
