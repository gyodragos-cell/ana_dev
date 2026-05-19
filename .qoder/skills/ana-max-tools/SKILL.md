---
name: ana-max-tools
description: Use ANA_MAX tools as sensory and operational extensions for desktop control, file operations, code analysis, browser automation, memory management, and security auditing. Automatically invoke when working with files, code, desktop tasks, web automation, or system operations. Triggers: file manipulation, code search, desktop screenshot, browser control, system info, security scan, memory save/search, terminal commands.
---

# ANA_MAX Tools Integration

Use ANA_MAX's 45 tools as your eyes, hands, and brain for complete system control.

## Quick Start

```python
from tools.qoder_ana_integration import ANAToolClient

ana = ANAToolClient()
```

**Server must be running**: `http://127.0.0.1:8765`
Start with: `python main.py --port 8765` in `ANA_MAX/`

## Tool Selection Guide

### When to use which tool:

| Task | Tool | Example |
|------|------|---------|
| **See screen** | `desktop_capture` | Before clicking on generic images/web |
| **Inspect Windows App UI** | `windows_uia_bridge` | Best for native Windows apps (0% error) |
| **Click/type on desktop** | `desktop_control` / `windows_uia_bridge` | GUI automation |
| **Read/write files** | `file_operations` | Code, configs, docs |
| **Search codebase** | `smart_search` | Find functions, patterns |
| **Understand code** | `codebase_understanding` | Architecture analysis |
| **Execute commands** | `terminal` | Run scripts, check status |
| **Browser automation** | `browser_control` | Web testing, scraping |
| **Save knowledge** | `ana_memory` | Lessons, patterns, configs |
| **Search memory** | `ana_memory` | Recall previous solutions |
| **System info** | `system_control` | OS, processes, resources |
| **Security audit** | `security_audit` | Scan secrets, vulnerabilities |
| **Network diagnostics** | `network_diag` | Ping, port scan, DNS |

## Desktop Control Workflow (The "Native UIA" Way vs OCR)

Pentru aplicații native Windows, preferă NATIVITATEA (`windows_uia_bridge`) în loc de capturi oarbe.

**1. Metoda UIA (Pentru aplicații Windows, FĂRĂ screenshots, perfect precis):**
```python
# Step 1: Inspect (Get all buttons, texts, menus)
ui_tree = ana.call_tool("windows_uia_bridge", action="inspect_window", window_title="Notepad")

# Step 2: Act (Click/Type precisely without coordinates)
ana.call_tool("windows_uia_bridge", action="type_text", window_title="Notepad", text="Hello!", auto_id="15")
```

**2. Metoda Veche OCR/Screenshot (Folosește doar dacă UIA dă greș):**
```python
# Step 1: See
screen = ana.call_tool("desktop_capture")
# Step 2: Act
ana.call_tool("desktop_control", action="click", x=400, y=300)
# Step 3: Verify
screen2 = ana.call_tool("desktop_capture")
```

**Desktop control actions:**
- `click` - Click at (x, y)
- `type` - Type text
- `drag` - Drag from (x1,y1) to (x2,y2)
- `scroll` - Scroll up/down
- `keypress` - Special keys (Enter, Ctrl+C, etc.)

## File Operations

**Best practices:**
- Always check if file exists before writing
- Use `action="read"` for reading
- Use `action="write"` for creating/overwriting
- Use `action="list"` for directories
- Use `edit` tool for surgical changes (preferred for code)

**Example:**
```python
# Read file
result = ana.call_tool("file_operations", action="read", path="config.py")

# List directory
files = ana.call_tool("file_operations", action="list", path="./src")

# Write file
ana.call_tool("file_operations", action="write", path="output.txt", content="data")
```

## Memory Usage (Your Long-Term Brain)

**Save important findings:**
```python
# Save lessons learned
ana.call_tool("ana_memory", 
    action="save", 
    content="Use smart_search before reading files manually",
    category="workflow")

# Save configurations
ana.call_tool("ana_memory",
    action="save",
    content="MCP server runs on port 8765",
    category="config")
```

**Search when needed:**
```python
# Recall previous solutions
result = ana.call_tool("ana_memory", action="search", query="authentication")
```

**Categories to use:**
- `workflow` - Process improvements
- `config` - System configurations
- `code` - Code patterns
- `errors` - Error solutions
- `security` - Security findings

## Code Search & Analysis

**Smart search first (fastest):**
```python
# Find authentication logic
ana.call_tool("smart_search", query="user authentication")

# Search with path constraint
ana.call_tool("smart_search", query="database connection", path="./core")
```

**Deep analysis:**
```python
# Understand entire codebase
ana.call_tool("codebase_understanding")

# Grep for patterns
ana.call_tool("grep_content", pattern="TODO|FIXME", path="./src")

# Find files by pattern
ana.call_tool("glob_search", pattern="*.py")
```

**Workflow:**
1. `smart_search` - Fast semantic search
2. `grep_content` - Exact pattern match
3. `file_operations` (read) - Read specific files
4. `codebase_understanding` - If need architecture view

## Browser Automation

**Complete workflow:**
```python
# Open page
ana.call_tool("browser_control", operation="open", url="https://example.com")

# Take screenshot
ana.call_tool("browser_control", operation="screenshot")

# Click element
ana.call_tool("browser_control", operation="click", selector="#login-btn")

# Type in field
ana.call_tool("browser_control", operation="type", 
    selector="#username", text="user@example.com")

# Get page content
ana.call_tool("browser_control", operation="get_content")
```

**Common operations:**
- `open` - Navigate to URL
- `click` - Click selector
- `type` - Type in selector
- `screenshot` - Capture page
- `get_content` - Get HTML/text
- `execute_js` - Run JavaScript

## Security & Network Tools

**Security audit:**
```python
# Scan for secrets in code
ana.call_tool("security_audit", 
    operation="scan_secrets", 
    target="./code")

# Static analysis
ana.call_tool("security_audit",
    operation="static_analysis",
    target="./app.py")
```

**Network diagnostics:**
```python
# Ping host
ana.call_tool("network_diag", operation="ping", target="google.com")

# Port scan
ana.call_tool("network_diag", operation="port_scan", target="127.0.0.1")

# DNS lookup
ana.call_tool("network_diag", operation="dns_lookup", target="example.com")
```

## Error Handling & Health Checks

**If tool fails:**
```python
# 1. Check server connection
if not ana.is_server_running():
    print("MCP Server not running!")
    # Instruct user: python main.py --port 8765

# 2. Run health check
ana.call_tool("tool_healthcheck")

# 3. List available tools
tools = ana.list_tools()
```

**Common errors:**
- `ConnectionError` → Server not running
- `Tool not found` → Check tool name with `list_tools()`
- `Timeout` → Tool execution taking too long, retry with simpler params

## Helper Scripts

Use these scripts from `.qoder/skills/ana-max-tools/scripts/`:

### Quick Test
```bash
python .qoder/skills/ana-max-tools/scripts/test_connection.py
```

### List Tools
```bash
python .qoder/skills/ana-max-tools/scripts/list_tools.py
```

### Desktop Capture
```bash
python .qoder/skills/ana-max-tools/scripts/capture_desktop.py
```

## Pro Tips

1. **Always see before acting** - Use `desktop_capture` before `desktop_control`
2. **Search before reading** - Use `smart_search` before `file_operations`
3. **Save what you learn** - Use `ana_memory` for reusable knowledge
4. **Verify after changes** - Capture/read again to confirm success
5. **Use autonomous mode** - For complex tasks: `autonomous_engine`

## Autonomous Mode

For multi-step tasks, let ANA plan and execute:
```python
ana.call_tool("autonomous_engine", 
    task="Create a Python web scraper that extracts product prices",
    max_steps=10)
```

## Response Parsing

All tools return:
```python
{
    "content": [{"text": "{JSON result}", "type": "text"}]
}
```

**Parse it:**
```python
import json
result = ana.call_tool("system_control")
data = json.loads(result["content"][0]["text"])
```

## Workflow Examples

### Example 1: Fix a bug
```python
# 1. Search for the code
ana.call_tool("smart_search", query="error handling login")

# 2. Read the file
ana.call_tool("file_operations", action="read", path="core/auth.py")

# 3. Make the fix
ana.call_tool("edit", ...)

# 4. Verify
ana.call_tool("file_operations", action="read", path="core/auth.py")
```

### Example 2: Automate desktop task
```python
# 1. See screen
ana.call_tool("desktop_capture")

# 2. Click target
ana.call_tool("desktop_control", action="click", x=500, y=300)

# 3. Type text
ana.call_tool("desktop_control", action="type", text="search query")

# 4. Press Enter
ana.call_tool("desktop_control", action="keypress", key="Enter")

# 5. Verify
ana.call_tool("desktop_capture")
```

### Example 3: Security audit
```python
# 1. Scan for secrets
ana.call_tool("security_audit", operation="scan_secrets", target=".")

# 2. Check network
ana.call_tool("network_diag", operation="port_scan", target="127.0.0.1")

# 3. Save findings
ana.call_tool("ana_memory", action="save", 
    content="No secrets found in codebase", 
    category="security")
```

## Additional Resources

- Complete guide: `tools/ANA_TOOLS_GUIDE.md` in ANA_MAX project
- Integration wrapper: `tools/qoder_ana_integration.py`
- Test script: `tools/test_ana_tools.py`
