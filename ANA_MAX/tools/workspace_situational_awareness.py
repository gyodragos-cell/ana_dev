import logging
import json
import time
import sys
import os
import subprocess
import ctypes
from typing import Dict, Any, List, Tuple
from pathlib import Path

from tools.base import Tool, ToolResult, ToolStatus, ToolDefinition, ToolParameter

logger = logging.getLogger(__name__)

GIT_STATUS_PREVIEW_LIMIT = 25


def _to_bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off"}:
            return False
    return default


class WorkspaceSituationalAwarenessTool(Tool):
    """Provides observation, git status, active UI app, recent log errors, and next-step recommendations."""

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="workspace_situational_awareness",
            description=(
                "Returns a compact JSON state containing active app/window, "
                "UIA quality, visible error signals, repo/git state, "
                "relevant open files if detectable, and a recommended next step."
            ),
            parameters=[
                ToolParameter(
                    name="include_git",
                    description="Include Git repository status and branch details (default: True)",
                    type="boolean",
                    required=False,
                    default="true"
                ),
                ToolParameter(
                    name="include_uia",
                    description="Include active app UI Automation details (default: True)",
                    type="boolean",
                    required=False,
                    default="true"
                ),
                ToolParameter(
                    name="include_errors",
                    description="Include recent warning and error log sweeps (default: True)",
                    type="boolean",
                    required=False,
                    default="true"
                )
            ],
            category="desktop"
        )

    def execute(self, **kwargs) -> ToolResult:
        include_git = _to_bool(kwargs.get("include_git"), True)
        include_uia = _to_bool(kwargs.get("include_uia"), True)
        include_errors = _to_bool(kwargs.get("include_errors"), True)

        # Determine workspace roots
        # Tools are in ANA_MAX/tools, so project root is two parents up from this file or parent of ANA_MAX
        base_path = Path(__file__).resolve().parent.parent
        workspace_root = base_path.parent

        try:
            state = {}

            # 1. UI and Window observation
            active_info = self._get_foreground_info(include_uia)
            state["active_ui"] = active_info

            # 2. Git repo observation
            if include_git:
                git_info = self._get_git_info(workspace_root)
                state["git"] = git_info
            else:
                state["git"] = {"enabled": False}

            # 3. Log errors sweep
            if include_errors:
                errors_info = self._get_recent_errors(base_path)
                state["log_signals"] = errors_info
            else:
                state["log_signals"] = {"enabled": False}

            # 4. Open files detection
            detected_files = self._detect_open_files(active_info.get("window_title", ""))
            state["open_files"] = detected_files

            # 5. Recommendation engine
            next_step = self._generate_recommendation(state)
            state["recommended_next_step"] = next_step

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=state,
                message="Workspace situational awareness successfully captured."
            )

        except Exception as e:
            logger.exception("Error executing workspace situational awareness")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Situational awareness sweep failed: {e}"
            )

    def _get_foreground_info(self, include_uia: bool) -> Dict[str, Any]:
        """Gets active app process, window title and measures UIA quality."""
        info = {
            "active_app": "Unknown",
            "window_title": "",
            "uia_quality": "LOW",
            "uia_elements_count": 0
        }

        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd:
                return info

            # Process Name
            pid = ctypes.c_ulong()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value:
                try:
                    import psutil
                    process = psutil.Process(pid.value)
                    info["active_app"] = process.name().replace(".exe", "")
                except Exception:
                    pass

            # Window Title
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buffer, length + 1)
                info["window_title"] = buffer.value

            # UIA Quality
            if include_uia:
                try:
                    from pywinauto import Desktop
                    start_time = time.time()
                    desktop = Desktop(backend="uia")
                    foreground = desktop.window(handle=hwnd)
                    
                    if foreground.exists():
                        # Quick descendant count check with absolute timeout of 1.5 seconds
                        descendants = []
                        desc_iter = foreground.descendants()
                        
                        # Fetch up to 100 elements to prevent UI freeze
                        for ctrl in desc_iter:
                            descendants.append(ctrl)
                            if len(descendants) >= 100 or (time.time() - start_time) > 1.5:
                                break

                        count = len(descendants)
                        info["uia_elements_count"] = count
                        if count > 0:
                            info["uia_quality"] = "HIGH" if count >= 10 else "MEDIUM"
                        else:
                            info["uia_quality"] = "MEDIUM"
                except Exception as e:
                    logger.debug(f"UIA analysis failed for handle {hwnd}: {e}")
                    info["uia_quality"] = "LOW"
            
            return info

        except Exception as e:
            logger.error(f"Failed to get active window info: {e}")
            return info

    def _get_git_info(self, workspace_root: Path) -> Dict[str, Any]:
        """Runs short Git operations to parse repo status."""
        git_info = {
            "is_repo": False,
            "repo_root": str(workspace_root),
            "branch": "Unknown",
            "status_summary": "",
            "status_preview": [],
            "changed_count": 0,
            "truncated": False,
            "clean": True
        }

        # Check if git is available
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
        except (subprocess.SubprocessError, FileNotFoundError):
            return git_info

        # Run Git status
        try:
            # 1. Branch
            res_branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(workspace_root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore"
            )
            if res_branch.returncode == 0:
                git_info["is_repo"] = True
                git_info["branch"] = res_branch.stdout.strip()

            # 2. Status
            res_status = subprocess.run(
                ["git", "status", "--short"],
                cwd=str(workspace_root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore"
            )
            if res_status.returncode == 0:
                git_info["is_repo"] = True
                status_out = res_status.stdout.strip()
                status_lines = status_out.splitlines() if status_out else []
                changed_count = len(status_lines)
                preview = status_lines[:GIT_STATUS_PREVIEW_LIMIT]
                git_info["changed_count"] = changed_count
                git_info["status_preview"] = preview
                git_info["truncated"] = changed_count > len(preview)
                git_info["status_summary"] = (
                    "clean"
                    if changed_count == 0
                    else f"{changed_count} changed paths; preview shows {len(preview)}"
                )
                git_info["clean"] = len(status_out) == 0

        except Exception as e:
            logger.warning(f"Git status query encountered error: {e}")

        return git_info

    def _get_recent_errors(self, base_path: Path) -> Dict[str, Any]:
        """Reads recent log file lines to parse error tracebacks or warnings."""
        signals = {
            "has_error_logs": False,
            "recent_errors_count": 0,
            "errors": []
        }

        log_file = base_path / "logs" / "ana_max.log"
        if not log_file.exists():
            return signals

        try:
            # Safe read last 50 lines
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                last_lines = lines[-50:]

            # Scan for anomalies
            error_keywords = ["ERROR", "CRITICAL", "Traceback", "Exception", "ModuleNotFoundError", "SyntaxError"]
            for idx, line in enumerate(last_lines):
                line_strip = line.strip()
                if any(kw in line_strip for kw in error_keywords):
                    signals["has_error_logs"] = True
                    # Extract context (e.g. current line + surrounding lines)
                    signals["errors"].append({
                        "line_num": len(lines) - len(last_lines) + idx + 1,
                        "content": line_strip[:150] # Keep it compact
                    })
            
            signals["recent_errors_count"] = len(signals["errors"])
            # Keep only the last 5 unique errors to keep JSON tiny
            signals["errors"] = signals["errors"][-5:]

        except Exception as e:
            logger.warning(f"Failed to read log file for errors analysis: {e}")

        return signals

    def _detect_open_files(self, window_title: str) -> List[str]:
        """Parses active window titles to extract current file base names."""
        if not window_title:
            return []

        open_files = []
        # Standard extensions
        extensions = [".py", ".md", ".json", ".js", ".html", ".css", ".txt", ".bat", ".ps1", ".yaml", ".yml"]
        
        # Split by typical IDE decorators/separators
        parts = []
        for sep in [" - ", " | ", " • ", " : "]:
            if sep in window_title:
                parts = window_title.split(sep)
                break
        
        if not parts:
            parts = window_title.split()

        for p in parts:
            p_clean = p.strip("* ")
            if any(p_clean.lower().endswith(ext) for ext in extensions):
                open_files.append(p_clean)

        return list(set(open_files))

    def _generate_recommendation(self, state: Dict[str, Any]) -> str:
        """Heuristic recommendation builder based on all observations."""
        git_clean = state.get("git", {}).get("clean", True)
        active_app = state.get("active_ui", {}).get("active_app", "Unknown")
        uia_quality = state.get("active_ui", {}).get("uia_quality", "LOW")
        has_log_errors = state.get("log_signals", {}).get("has_error_logs", False)
        open_files = state.get("open_files", [])

        # Heuristic 1: If there are Python tracebacks or critical log errors
        if has_log_errors:
            return (
                "Anomalies or Tracebacks detected in logs/ana_max.log. "
                "Review recent logs or run health checks to identify system errors."
            )

        # Heuristic 2: Uncommitted Git changes
        if not git_clean:
            git_state = state.get("git", {})
            changed_count = git_state.get("changed_count", 0)
            preview = git_state.get("status_preview", [])
            truncated = git_state.get("truncated", False)
            preview_text = "\n".join(preview[:10])
            if truncated:
                preview_text += "\n... output truncated; run git status --short for full list."
            return (
                f"Workspace is dirty with {changed_count} changed paths. "
                f"Preview:\n{preview_text}\n"
                "Verify correctness with RUN_ANA_QUALITY_GATE.bat before committing."
            )

        # Heuristic 3: Known editor in foreground but no open file detected
        if active_app in ["Code", "Cursor", "Notepad"] and not open_files:
            return f"Coding environment ({active_app}) in focus. No active source file detected in window title."

        # Heuristic 4: Coding environment with file open
        if open_files:
            return f"Focus is on editing {open_files[0]}. Continue development or run localized tests."

        # Default fallback
        return (
            "Workspace is clean and healthy. No critical blockers detected. "
            "Proceed with next planned feature or run system-wide quality gate checks."
        )
