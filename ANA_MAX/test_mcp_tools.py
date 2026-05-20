#!/usr/bin/env python3
"""Test MCP tools/list response"""
import sys
sys.path.insert(0, '.')

from mcp_stdio import load_tools, handle_request

# Load tools
count = load_tools()
print(f"Loaded {count} tools")

# Test tools/list
req = {'method': 'tools/list', 'id': 1}
resp = handle_request(req)

tools = resp['result']['tools']
print(f"\nFound {len(tools)} tools in MCP response:")

for i, tool in enumerate(tools[:5], 1):
    params_count = len(tool['inputSchema']['properties'])
    print(f"  {i}. {tool['name']}: {params_count} parameters")
    if params_count > 0:
        print(f"     Params: {', '.join(tool['inputSchema']['properties'].keys())}")

print(f"\n... and {len(tools) - 5} more tools")
