# ANA MAX - OpenCode Guidelines

You are interacting with the ANA MAX codebase. This is a highly optimized, agentic desktop automation system.

When generating code, analyzing bugs, or suggesting improvements, you MUST strictly adhere to the following architectural rules:

## 1. Native APIs over Subprocesses (Crucial for CPU)
- **NEVER** use `subprocess.run(["powershell"...])` to list processes, read files, or check system states. This causes massive CPU overhead and ruins the system's stealth/performance.
- Use `psutil` for any process/memory/system interactions.
- Use `pywinauto` (Microsoft UI Automation) for any GUI interaction. **Do not use OCR or blind screenshots for native Windows apps.**

## 2. Silent System (No Log Spam)
- Keep the console output clean. 
- Use `logger.debug()` for repetitive polling (e.g., checking new processes every 2 seconds, tracking mouse).
- Use `logger.info()` ONLY for major state changes (e.g., server start, initialization).

## 3. Persistent Connections (No Thrashing)
- Do not open and close the SQLite database (`memory.py`) repeatedly. Use the established Singleton connection `_conn` protected by `threading.Lock()`.

## 4. MCP Server Security
- The `mcp_server.py` exposes ANA MAX's God-Mode capabilities over HTTP.
- Ensure all new routes or commands are protected by the Bearer token (`auth_header != f"Bearer {api_key}"`). Never expose endpoints without authorization.

## 5. Tool Creation Workflow
If asked to create a new tool:
1. Create it in the `tools/` directory extending `tools.base.Tool`.
2. Implement `get_definition(self)`.
3. Register it in `tools/__init__.py`.
4. Add it to the tool arrays in `main.py` (`desktop_tools`, etc.).
5. Instruct the user to run `python main.py --test` to verify.
