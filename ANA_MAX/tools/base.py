"""
A.N.A. v18.0 MAX - Base Tool Classes
================================
Clase de baza pentru sistemul de tools.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type
import concurrent.futures
from enum import Enum
import logging
import inspect
import os

logger = logging.getLogger(__name__)


def _summarize_value(value: Any, max_len: int = 120) -> str:
    """Produce un rezumat scurt si sigur pentru logging."""
    text = repr(value)
    if len(text) > max_len:
        return f"<{type(value).__name__} len={len(text)}>"
    return text


def _summarize_kwargs(kwargs: Dict[str, Any]) -> Dict[str, str]:
    return {key: _summarize_value(value) for key, value in kwargs.items()}


class ToolStatus(Enum):
    """Status pentru rezultatul unui tool."""
    SUCCESS = "success"
    ERROR = "error"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    BLOCKED = "blocked"


@dataclass
class ToolResult:
    """Rezultatul executiei unui tool."""
    status: ToolStatus
    data: Any = None
    message: str = ""
    error: Optional[str] = None
    
    @property
    def is_success(self) -> bool:
        return self.status == ToolStatus.SUCCESS
    
    def __str__(self) -> str:
        if self.is_success:
            return str(self.data) if self.data else self.message
        return f"Error: {self.error or self.message}"


@dataclass
class ToolParameter:
    """Descrierea unui parametru pentru tool."""
    name: str
    description: str
    type: str = "string"
    required: bool = True
    default: Any = None
    choices: Optional[List[str]] = None


@dataclass
class ToolDefinition:
    """Definitia completa a unui tool pentru AI."""
    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)
    category: str = "general"
    requires_confirmation: bool = False
    dangerous: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Converteste la dict pentru AI (schema interna)."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                p.name: {
                    "description": p.description,
                    "type": p.type,
                    "required": p.required,
                    "default": p.default,
                    "choices": p.choices
                }
                for p in self.parameters
            }
        }

    def get_ollama_format(self) -> Dict[str, Any]:
        """Converteste la formatul Ollama/OpenAI compatibil."""
        properties = {}
        required = []
        for p in self.parameters:
            properties[p.name] = {
                "type": p.type if p.type != "any" else "string",
                "description": p.description
            }
            if p.choices:
                properties[p.name]["enum"] = p.choices
            if p.required:
                required.append(p.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }


import json
import datetime
import time

_manifest = None
def _load_permission_manifest():
    global _manifest
    if _manifest is not None:
        return _manifest
    
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "..", "config", "permission_manifest.json"),
        os.path.join("config", "permission_manifest.json"),
        "permission_manifest.json"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    _manifest = json.load(f)
                    return _manifest
            except Exception as e:
                logger.error(f"Error loading permission manifest: {e}")
                
    _manifest = {
        "global_settings": {"readonly_mode": False, "allowlist": []},
        "tools": {}
    }
    return _manifest


def _log_observability(tool_name: str, args: Dict[str, Any], start_time: float, latency: float, status: ToolStatus, error: Optional[str] = None):
    try:
        log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "observability.jsonl")
        
        masked_args = {}
        sensitive_keys = {"password", "token", "key", "api_key", "secret"}
        for k, v in args.items():
            if any(s in k.lower() for s in sensitive_keys):
                masked_args[k] = "********"
            else:
                masked_args[k] = _summarize_value(v, max_len=60)
                
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "tool": tool_name,
            "args": masked_args,
            "latency_sec": round(latency, 4),
            "status": status.value,
            "error": error
        }
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=True) + "\n")
    except Exception as e:
        logger.error(f"Failed to write observability log: {e}")


class Tool(ABC):
    """
    Clasa de baza pentru toate tool-urile.
    Fiecare tool trebuie sa implementeze execute() si get_definition().
    """
    
    @abstractmethod
    def get_definition(self) -> ToolDefinition:
        """Returneaza definitia tool-ului."""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Executa tool-ul cu argumentele date."""
        pass
    
    @property
    def name(self) -> str:
        """Numele tool-ului."""
        return self.get_definition().name
    
    @property
    def requires_confirmation(self) -> bool:
        """Daca necesita confirmare inainte de executie."""
        return self.get_definition().requires_confirmation
    
    def validate_params(self, **kwargs) -> Optional[str]:
        """Valideaza parametrii. Returneaza eroare sau None daca e OK."""
        definition = self.get_definition()
        
        for param in definition.parameters:
            if param.required and param.name not in kwargs:
                return f"Parametrul '{param.name}' este obligatoriu"
            
            if param.choices and param.name in kwargs:
                if kwargs[param.name] not in param.choices:
                    return f"Valoarea '{kwargs[param.name]}' nu e valida pentru '{param.name}'. Optiuni: {param.choices}"
        
        return None
    
    def safe_execute(self, **kwargs) -> ToolResult:
        """Executa cu validare si error handling."""
        manifest = _load_permission_manifest()
        global_settings = manifest.get("global_settings", {})
        tool_manifests = manifest.get("tools", {})
        
        tool_conf = tool_manifests.get(self.name, {})
        
        allowed = tool_conf.get("allowed", True)
        allowlist = global_settings.get("allowlist", [])
        
        if allowlist and self.name not in allowlist:
            allowed = False
            
        if not allowed:
            res = ToolResult(
                status=ToolStatus.BLOCKED,
                error=f"Tool-ul '{self.name}' este dezactivat prin permission manifest"
            )
            _log_observability(self.name, kwargs, time.time(), 0.0, ToolStatus.BLOCKED, res.error)
            return res
            
        global_readonly = global_settings.get("readonly_mode", False)
        is_tool_readonly = tool_conf.get("readonly", False)
        
        if global_readonly and not is_tool_readonly:
            res = ToolResult(
                status=ToolStatus.BLOCKED,
                error=f"Tool-ul '{self.name}' este blocat deoarece ruleaza in mod Read-Only"
            )
            _log_observability(self.name, kwargs, time.time(), 0.0, ToolStatus.BLOCKED, res.error)
            return res
            
        error = self.validate_params(**kwargs)
        if error:
            res = ToolResult(
                status=ToolStatus.ERROR,
                error=error
            )
            _log_observability(self.name, kwargs, time.time(), 0.0, ToolStatus.ERROR, error)
            return res
            
        requires_confirm = tool_conf.get("requires_confirmation", self.requires_confirmation)
        if requires_confirm:
            if not kwargs.get("confirm", False):
                res = ToolResult(
                    status=ToolStatus.REQUIRES_CONFIRMATION,
                    message=f"Tool-ul '{self.name}' necesita confirmare. Apeleaza cu confirm=True"
                )
                _log_observability(self.name, kwargs, time.time(), 0.0, ToolStatus.REQUIRES_CONFIRMATION, res.message)
                return res
        
        timeout = kwargs.get('timeout', 60)
        started_time = time.time()
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self.execute, **kwargs)
                res = future.result(timeout=timeout)
                latency = time.time() - started_time
                _log_observability(self.name, kwargs, started_time, latency, res.status, res.error or res.message if not res.is_success else None)
                return res
        except (concurrent.futures.TimeoutError, TimeoutError):
            logger.error(f"Timeout in {self.name} (> {timeout}s)")
            res = ToolResult(
                status=ToolStatus.ERROR,
                error=f"Timeout: Operatiunea {self.name} a durat prea mult (> {timeout}s)"
            )
            latency = time.time() - started_time
            _log_observability(self.name, kwargs, started_time, latency, ToolStatus.ERROR, res.error)
            return res
        except Exception as e:
            logger.error(f"Eroare in {self.name}: {e}")
            res = ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )
            latency = time.time() - started_time
            _log_observability(self.name, kwargs, started_time, latency, ToolStatus.ERROR, res.error)
            return res


class ToolRegistry:
    """
    Registru central pentru toate tool-urile.
    Permite inregistrare dinamica si lookup.
    """
    
    _instance: Optional['ToolRegistry'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: Dict[str, Tool] = {}
            cls._instance._categories: Dict[str, List[str]] = {}
        return cls._instance
    
    def register(self, tool: Tool) -> None:
        """Inregistreaza un tool."""
        definition = tool.get_definition()
        self._tools[definition.name] = tool
        
        # Adauga la categorie
        category = definition.category
        if category not in self._categories:
            self._categories[category] = []
        if definition.name not in self._categories[category]:
            self._categories[category].append(definition.name)
        
        logger.debug(f"Tool inregistrat: {definition.name} ({category})")
    
    def register_function(self, func: Callable, name: Optional[str] = None,
                          description: Optional[str] = None,
                          category: str = "general",
                          requires_confirmation: bool = False) -> None:
        """Inregistreaza o functie simpla ca tool."""
        
        tool_name = name or func.__name__
        tool_desc = description or func.__doc__ or f"Functia {tool_name}"
        
        # Extrage parametrii din semnatura functiei
        sig = inspect.signature(func)
        params = []
        for param_name, param in sig.parameters.items():
            params.append(ToolParameter(
                name=param_name,
                description=f"Parametrul {param_name}",
                required=param.default == inspect.Parameter.empty,
                default=None if param.default == inspect.Parameter.empty else param.default
            ))
        
        # Creeaza un wrapper Tool
        class FunctionTool(Tool):
            def __init__(self, fn, fn_name, fn_desc, fn_params, fn_cat, fn_confirm):
                self._func = fn
                self._name = fn_name
                self._desc = fn_desc
                self._params = fn_params
                self._cat = fn_cat
                self._confirm = fn_confirm
            
            def get_definition(self) -> ToolDefinition:
                return ToolDefinition(
                    name=self._name,
                    description=self._desc,
                    parameters=self._params,
                    category=self._cat,
                    requires_confirmation=self._confirm
                )
            
            def execute(self, **kwargs) -> ToolResult:
                try:
                    result = self._func(**kwargs)
                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data=result
                    )
                except Exception as e:
                    return ToolResult(
                        status=ToolStatus.ERROR,
                        error=str(e)
                    )
        
        tool = FunctionTool(func, tool_name, tool_desc, params, category, requires_confirmation)
        self.register(tool)
    
    def get(self, name: str) -> Optional[Tool]:
        """Obtine un tool dupa nume."""
        return self._tools.get(name)
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Alias pentru get()."""
        return self.get(name)
    
    def execute(self, name: str, **kwargs) -> ToolResult:
        """Executa un tool dupa nume."""
        tool = self.get(name)
        if not tool:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Tool-ul '{name}' nu exista"
            )
            
        # UI v17: Rich Feedback (disabled in MCP mode)
        if not os.environ.get('ANA_MCP_MODE'):
            clean_params = {k: (v if len(str(v)) < 100 else f"<{type(v).__name__} len={len(str(v))}>") for k, v in kwargs.items()}
            print(f"  Tool execution: {name}")
            print(f"  Params: {clean_params}")
            
        logger.info("TOOL START name=%s args=%s", name, _summarize_kwargs(kwargs))
        result = tool.safe_execute(**kwargs)
        if result.is_success:
            logger.info(
                "TOOL END name=%s status=%s message=%s",
                name,
                result.status.value,
                _summarize_value(result.message or result.data),
            )
        else:
            logger.warning(
                "TOOL END name=%s status=%s error=%s",
                name,
                result.status.value,
                _summarize_value(result.error or result.message),
            )
        return result
    
    def list_tools(self, category: Optional[str] = None) -> List[str]:
        """Listeaza toate tool-urile (optional filtrate pe categorie)."""
        if category:
            return self._categories.get(category, [])
        return list(self._tools.keys())
    
    def list_categories(self) -> List[str]:
        """Listeaza toate categoriile."""
        return list(self._categories.keys())

    def reset(self) -> None:
        """Reseteaza registrul pentru un nou runtime."""
        self._tools = {}
        self._categories = {}
    
    def get_all_definitions(self) -> List[Dict[str, Any]]:
        """Obtine definitiile tuturor tool-urilor (pentru AI)."""
        return [
            tool.get_definition().to_dict()
            for tool in self._tools.values()
        ]
    
    def get_tools_for_ai(self) -> List[Callable]:
        """Returneaza functiile pentru AI tool calling."""
        functions = []
        for tool in self._tools.values():
            def make_wrapper(t):
                def wrapper(**kwargs):
                    result = t.safe_execute(**kwargs)
                    return str(result)
                wrapper.__name__ = t.name
                wrapper.__doc__ = t.get_definition().description
                return wrapper
            functions.append(make_wrapper(tool))
        return functions


# Singleton pentru acces global
registry = ToolRegistry()
