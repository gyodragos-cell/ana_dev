#!/usr/bin/env python3
"""
ANA MAX - MCP stdio wrapper
Expune tool-urile ANA prin stdin/stdout pentru Kiro
"""
import sys
import json
import logging
import os
from pathlib import Path

# Enable MCP mode (disables rich console output)
os.environ['ANA_MCP_MODE'] = '1'

# Set UTF-8 encoding for all I/O
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Create logs directory and configure logging
log_dir = BASE_DIR / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.ERROR, filename=str(log_dir / 'mcp_stdio.log'))

from tools.base import registry

# Global flag for lazy loading
_tools_loaded = False

# Load all tools
def load_tools():
    """Load extended set of tools for better visibility (23 tools, ~6s startup)"""
    from tools.files import FilesTool
    from tools.system import SystemTool
    from tools.code import CodeTool
    from tools.web import WebTool
    from tools.git_tool import GitTool
    from tools.memory_tool import MemoryTool
    from tools.smart_search_tool import SmartSearchTool
    from tools.ana_context_tool import AnaContextTool
    
    # Vision & Desktop Control (pentru a vedea ce se întâmplă)
    from tools.desktop_capture import DesktopCaptureTool
    from tools.windows_uia_bridge import WindowsUiaBridgeTool
    from tools.foreground_ui_snapshot import ForegroundUISnapshotTool
    
    # Security & Process Inspection (pentru a vedea procesele)
    from tools.frida_automation import FridaTool
    from tools.windows_deep_sight import WindowsDeepSightTool
    from tools.security_tool import SecurityTool
    
    # Development & Terminal (pentru comenzi persistente)
    from tools.terminal_tool import TerminalTool
    from tools.debugger_tool import DebuggerTool
    from tools.edit_tool import EditTool
    
    # Productivity & Code (pentru task-uri și căutare)
    from tools.task_tool import TaskTool
    from tools.code_search import CodeSearchTool
    from tools.browser_control import BrowserControlTool
    
    # Premium Desktop Control (pentru testing)
    from tools.live_desktop_viewer import LiveDesktopViewerTool
    from tools.desktop_control_tool import DesktopControlTool
    from tools.windows_insight_tool import WindowsInsightTool
    
    tools = [
        # Core (8 tools - fast)
        FilesTool(),
        SystemTool(),
        CodeTool(),
        WebTool(),
        GitTool(),
        MemoryTool(),
        SmartSearchTool(),
        AnaContextTool(),
        
        # Vision & Desktop (3 tools - pentru vizibilitate)
        DesktopCaptureTool(),
        WindowsUiaBridgeTool(),
        ForegroundUISnapshotTool(),
        
        # Security & Inspection (3 tools - pentru procese)
        FridaTool(),
        WindowsDeepSightTool(),
        SecurityTool(),
        
        # Development (3 tools - pentru coding)
        TerminalTool(),
        DebuggerTool(),
        EditTool(),
        
        # Productivity (3 tools)
        TaskTool(),
        CodeSearchTool(),
        BrowserControlTool(),
        
        # Premium Desktop Control (3 tools - pentru testing)
        LiveDesktopViewerTool(),
        DesktopControlTool(),
        WindowsInsightTool(),
    ]
    
    for tool in tools:
        registry.register(tool)
    
    return len(tools)

def handle_request(request):
    """Handle MCP JSON-RPC request"""
    global _tools_loaded
    
    # Lazy load tools on first request
    if not _tools_loaded:
        load_tools()
        _tools_loaded = True
    
    method = request.get('method')
    params = request.get('params', {})
    req_id = request.get('id', 1)
    
    try:
        if method == 'initialize':
            return {
                'jsonrpc': '2.0',
                'id': req_id,
                'result': {
                    'protocolVersion': '2024-11-05',
                    'serverInfo': {
                        'name': 'ANA MAX',
                        'version': '1.0'
                    },
                    'capabilities': {
                        'tools': {
                            'listChanged': True
                        },
                        'resources': {
                            'listChanged': True
                        }
                    }
                }
            }
        
        elif method == 'tools/list':
            tools = []
            for name in registry.list_tools():
                tool = registry.get(name)
                if tool:
                    defn = tool.get_definition()
                    
                    # Build inputSchema from parameters
                    properties = {}
                    required = []
                    
                    for param in defn.parameters:
                        prop_schema = {'type': param.type, 'description': param.description}
                        
                        # Add enum/choices if available
                        if hasattr(param, 'choices') and param.choices:
                            prop_schema['enum'] = param.choices
                        
                        # Add default if available
                        if hasattr(param, 'default') and param.default is not None:
                            prop_schema['default'] = param.default
                        
                        properties[param.name] = prop_schema
                        
                        if param.required:
                            required.append(param.name)
                    
                    tools.append({
                        'name': name,
                        'description': defn.description,
                        'inputSchema': {
                            'type': 'object',
                            'properties': properties,
                            'required': required
                        }
                    })
            
            return {
                'jsonrpc': '2.0',
                'id': req_id,
                'result': {'tools': tools}
            }
        
        elif method == 'tools/call':
            tool_name = params.get('name')
            args = params.get('arguments', {})
            
            try:
                result = registry.execute(tool_name, **args)
                
                return {
                    'jsonrpc': '2.0',
                    'id': req_id,
                    'result': {
                        'content': [{
                            'type': 'text',
                            'text': json.dumps({
                                'success': result.is_success,
                                'data': result.data,
                                'message': result.message,
                                'error': result.error
                            }, default=str)
                        }]
                    }
                }
            except Exception as e:
                return {
                    'jsonrpc': '2.0',
                    'id': req_id,
                    'result': {
                        'content': [{
                            'type': 'text',
                            'text': json.dumps({
                                'success': False,
                                'data': None,
                                'message': f'Tool execution error: {str(e)}',
                                'error': str(e)
                            })
                        }]
                    }
                }
        
        elif method == 'resources/list':
            # Return empty resources list (we only have tools)
            return {
                'jsonrpc': '2.0',
                'id': req_id,
                'result': {'resources': []}
            }
        
        else:
            return {
                'jsonrpc': '2.0',
                'id': req_id,
                'error': {'code': -32601, 'message': f'Method not found: {method}'}
            }
    
    except Exception as e:
        return {
            'jsonrpc': '2.0',
            'id': req_id,
            'error': {'code': -32603, 'message': str(e)}
        }

def main():
    """Main stdio loop"""
    # Read requests from stdin (tools loaded lazily on first request)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            request = json.loads(line)
            response = handle_request(request)
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            print(json.dumps({
                'jsonrpc': '2.0',
                'id': None,
                'error': {'code': -32700, 'message': 'Parse error'}
            }), flush=True)
        except Exception as e:
            print(json.dumps({
                'jsonrpc': '2.0',
                'id': None,
                'error': {'code': -32603, 'message': str(e)}
            }), flush=True)

if __name__ == '__main__':
    main()
