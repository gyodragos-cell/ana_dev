#!/usr/bin/env python3
"""Fix BOM (Byte Order Mark) issues in Python files"""
import sys
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

files_to_fix = [
    Path(__file__).parent / "tools" / "jules_mcp_bridge.py",
    Path(__file__).parent / "tools" / "verdent_tools.py",
    Path(__file__).parent / "core" / "backends" / "router.py",
]

print("Fixing BOM issues...")
for file_path in files_to_fix:
    if not file_path.exists():
        print(f"  âš ï¸  File not found: {file_path}")
        continue

    # Read file as bytes
    with open(file_path, 'rb') as f:
        content = f.read()

    # Check for BOM
    if content.startswith(b'\xef\xbb\xbf'):
        # Remove BOM
        content = content[3:]
        with open(file_path, 'wb') as f:
            f.write(content)
        print(f"  âœ… Fixed BOM: {file_path.name}")
    else:
        print(f"  âœ… No BOM: {file_path.name}")

print("\nAll files fixed!")
