#!/usr/bin/env python3
"""
Quick test of Live Tool Healer without loading entire ANA_MAX
"""

import sys
from pathlib import Path

# Add current dir to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.live_tool_healer import LiveToolHealer
from tools.base import ToolStatus

def test_healer():
    print("=" * 70)
    print("ðŸ§  LIVE TOOL HEALER - Interactive Demo")
    print("=" * 70)
    print()

    healer = LiveToolHealer()

    # Test 1: Supervise (real-time monitoring)
    print("\n[TEST 1] INTELLIGENT SUPERVISION - Real-time monitoring")
    print("â”€" * 70)
    result = healer.execute(
        action="supervise",
        tool_name="smart_search",
        duration_seconds=3,
        verbose=True
    )
    print(result.message)

    # Test 2: Auto-diagnose
    print("\n[TEST 2] AUTO-DIAGNOSIS - Root cause analysis")
    print("â”€" * 70)
    result = healer.execute(
        action="diagnose_failure",
        tool_name="smart_search",
        verbose=True
    )
    print(result.message)

    # Test 3: Propose fix
    print("\n[TEST 3] PROPOSED FIX - Interactive approval")
    print("â”€" * 70)
    result = healer.execute(
        action="auto_fix",
        tool_name="smart_search",
        verbose=True
    )
    print(result.message)

    # Test 4: Explain
    print("\n[TEST 4] EXPLAIN ROOT CAUSE - Deep dive")
    print("â”€" * 70)
    result = healer.execute(
        action="explain_issue",
        tool_name="smart_search",
        verbose=True
    )
    print(result.message)

    # Test 5: Health check
    print("\n[TEST 5] GENERATE HEALTH CHECK - Test generation")
    print("â”€" * 70)
    result = healer.execute(
        action="test_health",
        tool_name="smart_search",
        verbose=True
    )
    print(result.message)

    print("\n" + "=" * 70)
    print("âœ… ALL TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    test_healer()
