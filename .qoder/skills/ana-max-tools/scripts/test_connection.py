#!/usr/bin/env python3
"""
Quick test to verify ANA_MAX MCP Server connection
"""

import sys
from pathlib import Path

# Add ANA_MAX to path
ana_max_dir = Path(__file__).resolve().parents[4] / "ANA_MAX"
sys.path.insert(0, str(ana_max_dir))

from tools.qoder_ana_integration import ANAToolClient

def main():
    print("Testing ANA_MAX MCP Server connection...\n")
    
    ana = ANAToolClient()
    
    if ana.is_server_running():
        print("✓ MCP Server is running!")
        
        tools = ana.list_tools()
        tool_list = tools.get('result', {}).get('tools', [])
        print(f"✓ Available tools: {len(tool_list)}")
        print(f"✓ Server URL: {ana.base_url}")
        print("\nReady to use ANA_MAX tools!")
        return 0
    else:
        print("✗ MCP Server is NOT running!")
        print("\nTo start:")
        print("  cd ANA_MAX")
        print("  python main.py --port 8765")
        return 1

if __name__ == "__main__":
    sys.exit(main())
