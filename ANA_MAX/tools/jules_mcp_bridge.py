"""
Jules MCP Bridge Tool
=====================
Conecteaza ANA MAX la Jules MCP Server pentru a delega task-uri de coding.

Features:
- API Key Rotation pentru acces nelimitat
- Multiple keys configurabile
- Auto-recovery la rate limit
- Health check și statistici

Tool-urile Jules disponibile:
- create_coding_task: Creeaza task-uri de coding (bug fix, features, tests)
- manage_session: Aproba/respinge planuri, trimite mesaje
- get_session_status: Verifica statusul unei sesiuni
- schedule_recurring_task: Programeaza task-uri recurente
- delete_schedule: Sterge un schedule
- list_schedules: Listeaza toate schedule-urile
- wait_for_session: Asteapta finalizarea unei sesiuni
- get_activities_since: Obține activitati dintr-o sesiune
- delete_session: Sterge o sesiune
- get_source_details: Obține detalii despre repository
- add_api_key: Adauga un API key nou pentru rotație
- list_api_keys: Listeaza toate API keys
- get_key_stats: Statistici utilizare keys

Author: ANA MAX Integration
Date: 2026-05-19
"""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from tools.base import Tool, ToolDefinition, ToolParameter, ToolResult, ToolStatus

logger = logging.getLogger(__name__)

JULES_MCP_PATH = Path(r"C:\Users\billy\Desktop\jules\jules-mcp-server-main")
JULES_DIST = JULES_MCP_PATH / "dist" / "index.js"


class JulesMCPTool(Tool):
    """Bridge catre Jules MCP Server - permite ANA sa foloseasca Jules pentru coding tasks."""

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="jules_mcp_bridge",
            description="Delega task-uri de coding catre Jules (Google AI coding agent) cu API Key Rotation. Actiuni: create_task, manage_session, get_status, schedule_task, add_api_key, list_api_keys, get_key_stats.",
            parameters=[
                ToolParameter(
                    name="action",
                    description="Actiunea: create_task, manage_session, get_status, schedule_task, list_schedules, wait_for_session, get_activities, delete_session, get_source_details, list_sources, add_api_key, list_api_keys, get_key_stats, reset_keys",
                    type="string",
                    required=True,
                    choices=[
                        "create_task", "manage_session", "get_status",
                        "schedule_task", "list_schedules", "delete_schedule",
                        "wait_for_session", "get_activities", "delete_session",
                        "get_source_details", "list_sources",
                        "add_api_key", "list_api_keys", "get_key_stats", "reset_keys"
                    ]
                ),
                ToolParameter(
                    name="prompt",
                    description="Descrierea task-ului in limbaj natural (pentru create_task, schedule_task)",
                    type="string",
                    required=False,
                ),
                ToolParameter(
                    name="session_id",
                    description="ID-ul sesiunii Jules",
                    type="string",
                    required=False,
                ),
                ToolParameter(
                    name="source",
                    description="Repository (format: sources/github/owner/repo)",
                    type="string",
                    required=False,
                ),
                ToolParameter(
                    name="action_type",
                    description="Tip actiune pentru manage_session: approve_plan, send_message, reject_plan",
                    type="string",
                    required=False,
                ),
                ToolParameter(
                    name="message",
                    description="Mesaj de trimis",
                    type="string",
                    required=False,
                ),
                ToolParameter(
                    name="api_key",
                    description="API key nou (pentru add_api_key)",
                    type="string",
                    required=False,
                ),
                ToolParameter(
                    name="key_name",
                    description="Nume pentru API key",
                    type="string",
                    required=False,
                ),
                ToolParameter(
                    name="cron_expression",
                    description="Cron expression (ex: '0 9 * * 1' = Luni 9 AM)",
                    type="string",
                    required=False,
                ),
                ToolParameter(
                    name="task_name",
                    description="Nume pentru schedule",
                    type="string",
                    required=False,
                ),
                ToolParameter(
                    name="branch",
                    description="Git branch (default: main)",
                    type="string",
                    required=False,
                ),
                ToolParameter(
                    name="auto_create_pr",
                    description="Creeaza PR automat (default: true)",
                    type="boolean",
                    required=False,
                ),
                ToolParameter(
                    name="require_plan_approval",
                    description="Cere aprobare (default: false)",
                    type="boolean",
                    required=False,
                ),
            ],
            category="jules_integration"
        )

    def execute(self, action: str, **kwargs) -> ToolResult:
        """Executa o actiune prin Jules MCP Server."""
        try:
            # Gestionare API Keys (nu necesita Jules MCP)
            if action == "add_api_key":
                from tools.jules_api_rotator import add_api_key
                api_key = kwargs.get("api_key", "")
                key_name = kwargs.get("key_name", "")
                
                if not api_key:
                    return ToolResult(
                        status=ToolStatus.ERROR,
                        error="API key is required for add_api_key action"
                    )
                
                success = add_api_key(api_key, key_name)
                if success:
                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        message=f"API key added successfully: {key_name or api_key[-8:]}"
                    )
                else:
                    return ToolResult(
                        status=ToolStatus.ERROR,
                        error="API key already exists"
                    )
            
            elif action == "list_api_keys":
                from tools.jules_api_rotator import get_rotator
                rotator = get_rotator()
                keys = rotator.list_keys()
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={"keys": keys},
                    message=f"Found {len(keys)} API keys configured"
                )
            
            elif action == "get_key_stats":
                from tools.jules_api_rotator import get_rotator
                rotator = get_rotator()
                stats = rotator.get_stats()
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=stats,
                    message="API key statistics retrieved"
                )
            
            elif action == "reset_keys":
                from tools.jules_api_rotator import get_rotator
                rotator = get_rotator()
                rotator.reset_all_counts()
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    message="All API key counts have been reset"
                )
            
            # Verifica daca Jules MCP e instalat
            if not JULES_DIST.exists():
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error="Jules MCP Server nu este build-uit. Ruleaza: npm run build in " + str(JULES_MCP_PATH)
                )

            # Obține API key din rotator
            from tools.jules_api_rotator import get_next_api_key
            api_key = get_next_api_key()
            if not api_key:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error="No active API keys available. Add keys using add_api_key action."
                )

            # Pregateste payload-ul MCP
            mcp_payload = self._build_mcp_payload(action, **kwargs)
            
            # Executa Jules MCP prin stdio cu API key-ul curent
            result = self._call_jules_mcp(mcp_payload, api_key)
            
            if result:
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=result,
                    message=f"Jules action '{action}' executata cu succes"
                )
            else:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error="Jules MCP nu a returnat un rezultat valid"
                )

        except Exception as e:
            logger.error(f"Jules MCP execution failed: {e}", exc_info=True)
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Jules MCP execution failed: {str(e)}"
            )

    def _build_mcp_payload(self, action: str, **kwargs) -> Dict[str, Any]:
        """Construieste payload-ul pentru Jules MCP."""
        
        if action == "create_task":
            return {
                "method": "tools/call",
                "params": {
                    "name": "create_coding_task",
                    "arguments": {
                        "prompt": kwargs.get("prompt", ""),
                        "source": kwargs.get("source", ""),
                        "branch": kwargs.get("branch", "main"),
                        "auto_create_pr": kwargs.get("auto_create_pr", True),
                        "require_plan_approval": kwargs.get("require_plan_approval", False),
                        "title": kwargs.get("title", None)
                    }
                }
            }
        
        elif action == "manage_session":
            return {
                "method": "tools/call",
                "params": {
                    "name": "manage_session",
                    "arguments": {
                        "session_id": kwargs.get("session_id", ""),
                        "action": kwargs.get("action_type", ""),
                        "message": kwargs.get("message", None)
                    }
                }
            }
        
        elif action == "get_status":
            return {
                "method": "tools/call",
                "params": {
                    "name": "get_session_status",
                    "arguments": {
                        "session_id": kwargs.get("session_id", "")
                    }
                }
            }
        
        elif action == "schedule_task":
            return {
                "method": "tools/call",
                "params": {
                    "name": "schedule_recurring_task",
                    "arguments": {
                        "task_name": kwargs.get("task_name", ""),
                        "cron_expression": kwargs.get("cron_expression", ""),
                        "prompt": kwargs.get("prompt", ""),
                        "source": kwargs.get("source", "")
                    }
                }
            }
        
        elif action == "list_schedules":
            return {
                "method": "tools/call",
                "params": {
                    "name": "list_schedules",
                    "arguments": {}
                }
            }
        
        elif action == "wait_for_session":
            return {
                "method": "tools/call",
                "params": {
                    "name": "wait_for_session",
                    "arguments": {
                        "session_id": kwargs.get("session_id", ""),
                        "timeout_seconds": kwargs.get("timeout_seconds", 300),
                        "poll_interval_seconds": kwargs.get("poll_interval_seconds", 10)
                    }
                }
            }
        
        elif action == "get_activities":
            return {
                "method": "tools/call",
                "params": {
                    "name": "get_activities_since",
                    "arguments": {
                        "session_id": kwargs.get("session_id", ""),
                        "since": kwargs.get("since", "")
                    }
                }
            }
        
        elif action == "delete_session":
            return {
                "method": "tools/call",
                "params": {
                    "name": "delete_session",
                    "arguments": {
                        "session_id": kwargs.get("session_id", "")
                    }
                }
            }
        
        elif action == "get_source_details":
            return {
                "method": "tools/call",
                "params": {
                    "name": "get_source_details",
                    "arguments": {
                        "source_name": kwargs.get("source", "")
                    }
                }
            }
        
        elif action == "list_sources":
            return {
                "method": "resources/read",
                "params": {
                    "uri": "jules://sources"
                }
            }
        
        else:
            raise ValueError(f"Unknown action: {action}")

    def _call_jules_mcp(self, payload: Dict[str, Any], api_key: str) -> Optional[Dict[str, Any]]:
        """Apeleaza Jules MCP Server prin stdio."""
        try:
            # Seteaza variabilele de mediu din .env cu API key-ul curent
            env = self._load_env()
            env["JULES_API_KEY"] = api_key  # Override cu key-ul din rotator
            
            # Ruleaza Jules MCP
            proc = subprocess.run(
                ["node", str(JULES_DIST)],
                input=json.dumps(payload) + "\n",
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
                cwd=str(JULES_MCP_PATH)
            )
            
            if proc.returncode == 0 and proc.stdout:
                # Parseaza raspunsul
                for line in proc.stdout.strip().split("\n"):
                    if line.strip():
                        try:
                            result = json.loads(line)
                            # Record successful request
                            from tools.jules_api_rotator import get_rotator
                            get_rotator().record_request(api_key, success=True)
                            return result
                        except json.JSONDecodeError:
                            continue
            
            # Request failed
            error_msg = proc.stderr[:500] if proc.stderr else "Unknown error"
            from tools.jules_api_rotator import get_rotator
            get_rotator().record_request(api_key, success=False, error=error_msg)
            
            if proc.stderr:
                logger.warning(f"Jules MCP stderr: {error_msg}")
            
            return None

        except subprocess.TimeoutExpired:
            logger.error("Jules MCP call timed out")
            from tools.jules_api_rotator import get_rotator
            get_rotator().record_request(api_key, success=False, error="Timeout")
            return None
        except Exception as e:
            logger.error(f"Jules MCP call failed: {e}")
            from tools.jules_api_rotator import get_rotator
            get_rotator().record_request(api_key, success=False, error=str(e))
            return None

    def _load_env(self) -> Dict[str, str]:
        """Incarca variabilele de mediu din .env."""
        env_file = JULES_MCP_PATH / ".env"
        env = os.environ.copy()
        
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env[key.strip()] = value.strip()
        
        return env
