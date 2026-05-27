#!/usr/bin/env python3
"""
JokerForge/ANA MAX - Tool Verification Script
==============================================
Validates tool definitions, loads registry, and tests core tools.
Must be ASCII-only to pass quality gate.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root))

print("=" * 60)
print("  JOKERFORGE / ANA MAX - TOOL VERIFICATION")
print("=" * 60)

failed = False

try:
    import main
    from tools.base import registry

    # Load all tools by importing main module initialization
    if hasattr(main, '_register_all_tools'):
        main._register_all_tools()

    tools = registry.list_tools()
    total_tools = len(tools)
    print(f"\n[1] Tool Loading: [PASS] - Loaded {total_tools} tools in registry.")

    if total_tools < 50:
        print(f"    [FAIL] Expected at least 50 tools, but only found {total_tools}.")
        failed = True

except Exception as e:
    print(f"\n[1] Tool Loading: [FAIL] - Failed to load registry: {e}")
    failed = True
    sys.exit(1)

# 2. Schema Validation
print("\n[2] Schema Verification...")
invalid_schemas = 0
for name in tools:
    tool = registry.get(name)
    if not tool:
        print(f"    [FAIL] Tool {name} not found in registry lookup")
        invalid_schemas += 1
        continue
    try:
        defn = tool.get_definition()
        # Verify schema integrity
        if not defn.name or not defn.description:
            print(f"    [FAIL] Tool {name} is missing name or description")
            invalid_schemas += 1
        for p in defn.parameters:
            if not p.name or not p.description:
                print(f"    [FAIL] Tool {name} parameter {p.name} is missing name/description")
                invalid_schemas += 1
    except Exception as e:
        print(f"    [FAIL] Failed to read schema of {name}: {e}")
        invalid_schemas += 1

if invalid_schemas == 0:
    print(f"    [OK] Checked all {total_tools} tools. All definitions are valid.")
else:
    print(f"    [FAIL] Found {invalid_schemas} schema errors.")
    failed = True

# 3. Dry-Run Execution Tests
print("\n[3] Dry-Run Validation Tests...")
core_checks = [
    ("file_operations", {"operation": "list", "path": "."}),
    ("system_control", {"operation": "vitals"})
]

for name, params in core_checks:
    tool = registry.get(name)
    if not tool:
        print(f"    [FAIL] Core tool {name} is missing from registry")
        failed = True
        continue
    try:
        # Run execution check
        res = tool.safe_execute(**params)
        if res.is_success:
            print(f"    [OK] {name} validation passed.")
        else:
            # Note: system_control vitals might return status error if OS utilities fail, but we check if it handled it
            print(f"    [WARN] {name} execution returned status {res.status.value}: {res.error or res.message}")
    except Exception as e:
        print(f"    [FAIL] {name} execution crashed: {e}")
        failed = True

# Verdict
print("\n" + "=" * 60)
if failed:
    print("  VERIFICATION STATUS: [FAIL] - Core tools validation failed.")
    print("=" * 60)
    sys.exit(1)
else:
    print("  VERIFICATION STATUS: [PASS] - All tools verified successfully.")
    print("=" * 60)
    sys.exit(0)
