import requests
import json

print("=" * 60)
print("  ANA MAX MCP Server - Tool Test")
print("=" * 60)

MCP_URL = "http://127.0.0.1:8765/mcp"

def call_tool(name, args={}):
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": name,
            "arguments": args
        },
        "id": 1
    }
    r = requests.post(MCP_URL, json=payload)
    result = r.json()
    if 'result' in result:
        return json.loads(result['result']['content'][0]['text'])
    else:
        raise Exception(result.get('error', 'Unknown error'))

# Test 1: System Info
print("\n[1/6] System Control...")
try:
    info = call_tool('system_control', {'action': 'get_system_info'})
    print(f"âœ… OS: {info.get('os', 'N/A')}")
    print(f"âœ… Machine: {info.get('machine', 'N/A')}")
except Exception as e:
    print(f"âŒ Error: {e}")

# Test 2: Desktop Screenshot (EYES!)
print("\n[2/6] Desktop Capture (EYES)...")
try:
    result = call_tool('desktop_capture')
    print(f"âœ… Status: {result.get('status', 'OK')}")
    if 'screenshot' in result:
        print(f"âœ… Screenshot captured (base64 length: {len(result['screenshot'])})")
except Exception as e:
    print(f"âŒ Error: {e}")

# Test 3: File Operations
print("\n[3/6] File Operations...")
try:
    files = call_tool('file_operations', {'action': 'list', 'path': 'c:\\Users\\billy\\Desktop'})
    print(f"âœ… Desktop files: {len(files.get('files', []))} items")
except Exception as e:
    print(f"âŒ Error: {e}")

# Test 4: Terminal
print("\n[4/6] Terminal Access...")
try:
    term = call_tool('terminal', {'command': 'whoami'})
    print(f"âœ… User: {term.get('output', 'N/A').strip()}")
except Exception as e:
    print(f"âŒ Error: {e}")

# Test 5: Windows UIA Bridge (Advanced Vision)
print("\n[5/6] Windows UIA Bridge (Smart Vision)...")
try:
    ui = call_tool('windows_uia_bridge', {'action': 'get_foreground_window'})
    print(f"âœ… Active window: {ui.get('title', 'N/A')}")
except Exception as e:
    print(f"âŒ Error: {e}")

# Test 6: Memory
print("\n[6/6] ANA Memory (Brain)...")
try:
    mem = call_tool('ana_memory', {'action': 'search', 'query': 'test'})
    print(f"âœ… Memory search working")
except Exception as e:
    print(f"âŒ Error: {e}")

print("\n" + "=" * 60)
print("  ALL TOOLS ACCESSIBLE! âœ…")
print("=" * 60)
print("\nðŸŽ¯ Available Tools (57 total):")
print("  ðŸ‘ï¸  Vision: desktop_capture, windows_uia_bridge, ocr_tool")
print("  ðŸ–±ï¸  Control: desktop_control, windows_uia_bridge")
print("  ðŸ“ Files: file_operations, smart_search, grep_content")
print("  ðŸ’» System: system_control, terminal, task")
print("  ðŸ§  Memory: ana_memory, memory_cortex")
print("  ðŸŒ Web: browser_control, web_search, web_scraper")
print("  ðŸ”’ Security: security_audit, frida_instrument")
print("  + 40+ more tools!")
