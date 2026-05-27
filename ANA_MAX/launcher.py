"""
ANA MAX Launcher — Pornire sigura cu verificare integritate si auto-recovery.
Ruleaza: python launcher.py [--port 8766] [--host 127.0.0.1] [--admin]
"""

import sys, os, json, time, subprocess, signal, socket, tempfile, shutil
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).parent.resolve()
LOG_DIR = BASE_DIR / "logs"
PORT = 8766
HOST = "127.0.0.1"
SERVER_SCRIPT = BASE_DIR / "main.py"
VENV_PYTHON = BASE_DIR / "venv" / "Scripts" / "python.exe"
HEALTH_TIMEOUT = 15
MAX_RETRIES = 2
STATE_FILE = BASE_DIR / ".launcher_state.json"

REQUIRED_FILES = [
    "main.py",
    "tools/base.py",
    "tools/windows_deep_sight.py",
]

REQUIRED_DIRS = [
    "tools",
    "logs",
    "data",
]


def _log(msg: str):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def _check_files() -> list[str]:
    missing = []
    for f in REQUIRED_FILES:
        if not (BASE_DIR / f).exists():
            missing.append(f)
    for d in REQUIRED_DIRS:
        if not (BASE_DIR / d).is_dir():
            missing.append(d)
    return missing


def _try_python() -> Optional[Path]:
    for exe in [VENV_PYTHON, Path("python.exe"), Path("python3.exe")]:
        if exe.exists():
            try:
                r = subprocess.run([str(exe), "--version"], capture_output=True, text=True, timeout=5)
                if r.returncode == 0:
                    return exe
            except Exception:
                continue
    return None


def _port_free(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            return s.connect_ex((HOST, port)) != 0
    except Exception as e:
        return True


def _kill_port(port: int):
    # First try: normal kill (works for non-elevated processes)
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | "
             f"ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force }}" ],
            capture_output=True, text=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        time.sleep(2)
    except Exception as e:
        pass

    # If still occupied, try elevated kill (UAC prompt)
    if not _port_free(port):
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 f"$p = Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue; "
                 f"if ($p) {{ Start-Process taskkill -ArgumentList '/F','/PID',$p.OwningProcess -Verb RunAs -Wait }}" ],
                capture_output=True, text=True, timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(3)
        except Exception as e:
            pass


def _mcp_tools_list(timeout: int = HEALTH_TIMEOUT) -> Optional[list[dict]]:
    import urllib.request
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}
    }).encode()
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            req = urllib.request.Request(
                f"http://{HOST}:{PORT}/mcp",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read())
                tools = data.get("result", {}).get("tools")
                if isinstance(tools, list):
                    return tools
        except Exception:
            time.sleep(1)
    return None


def _mcp_call(tool: str, arguments: dict, timeout: int = HEALTH_TIMEOUT) -> Optional[dict]:
    import urllib.request
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000) % 100000,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    }).encode()
    try:
        req = urllib.request.Request(
            f"http://{HOST}:{PORT}/mcp",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            text = data.get("result", {}).get("content", [{}])[0].get("text", "")
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def _smart_readiness(timeout: int = HEALTH_TIMEOUT) -> tuple[bool, str]:
    tools = _mcp_tools_list(timeout=timeout)
    if tools is None:
        return False, "tools/list unavailable"

    names = {str(tool.get("name")) for tool in tools if isinstance(tool, dict)}
    if "tool_router" not in names:
        return False, "tool_router missing from tools/list"
    if "agent_coach" not in names:
        return False, "agent_coach missing from tools/list"

    agent_schema = next((tool for tool in tools if tool.get("name") == "agent_coach"), {})
    actions = (
        agent_schema.get("inputSchema", {})
        .get("properties", {})
        .get("action", {})
        .get("enum", [])
    )
    if "recommend" not in actions:
        return False, "agent_coach action=recommend missing from schema"

    router = _mcp_call(
        "tool_router",
        {
            "task": "MCP tool failed with schema mismatch action versus operation",
            "error": "Invalid value for operation",
            "max_tools": 4,
        },
        timeout=timeout,
    )
    router_data = router.get("data", {}) if isinstance(router, dict) else {}
    if not (router and router.get("success") and router_data.get("recommended_tools")):
        return False, "tool_router call did not return recommendations"

    coach = _mcp_call(
        "agent_coach",
        {
            "action": "recommend",
            "task": "MCP tool failed with schema mismatch action versus operation",
            "error": "Invalid value for operation",
            "max_tools": 5,
            "include_prompt": False,
        },
        timeout=timeout,
    )
    coach_data = coach.get("data", {}) if isinstance(coach, dict) else {}
    if not (
        coach
        and coach.get("success")
        and coach_data.get("schema") == "ana.agent_coach.recommend.v1"
        and coach_data.get("primary_tool")
    ):
        return False, "agent_coach action=recommend did not return primary_tool"

    return True, f"smart ready: {len(tools)} tools, primary={coach_data.get('primary_tool')}"


def _health_check(timeout: int = HEALTH_TIMEOUT) -> bool:
    ok, _message = _smart_readiness(timeout=timeout)
    return ok


def _tool_count(timeout: int = 3) -> Optional[int]:
    tools = _mcp_tools_list(timeout=timeout)
    if tools is None:
        return None
    return len(tools)


def _load_state() -> dict:
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
    except Exception as e:
        pass
    return {"boot_count": 0, "last_ok": None, "retries": 0}


def _save_state(state: dict):
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2))
    except Exception as e:
        pass


def start_server(python_exe: Path, port: int = PORT, host: str = HOST,
                 admin: bool = False) -> Optional[subprocess.Popen]:
    cmd = [str(python_exe), str(SERVER_SCRIPT), "--port", str(port), "--host", host]
    if admin:
        import ctypes
        if ctypes.windll.shell32.IsUserAnAdmin():
            _log("Deja admin. Pornire directa.")
            return subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW, cwd=str(BASE_DIR)
            )
        _log("Lansez fereastra UAC... Accepta dialogul pentru a continua.")
        ps_admin = (
            f'Start-Process -FilePath "{python_exe}" '
            f'-ArgumentList \'{SERVER_SCRIPT} --port {port} --host {host}\' '
            f'-Verb RunAs -WindowStyle Normal -PassThru'
        )
        proc = subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", ps_admin],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return proc

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
        cwd=str(BASE_DIR)
    )
    return proc


def main():
    global HOST, PORT
    port = PORT
    host = HOST
    admin = False

    import ctypes

    for arg in sys.argv[1:]:
        if arg == "--admin":
            admin = True
        elif arg.startswith("--port="):
            port = int(arg.split("=")[1])
        elif arg.startswith("--host="):
            host = arg.split("=")[1]

    PORT = port
    HOST = host

    _log("=== ANA MAX Launcher ===")
    state = _load_state()
    state["boot_count"] = state.get("boot_count", 0) + 1
    _save_state(state)

    # Step 1: Verifica fisiere si creeaza directoare lipsa
    _log("Verific fisiere...")
    for d in REQUIRED_DIRS:
        (BASE_DIR / d).mkdir(parents=True, exist_ok=True)
    missing = _check_files()
    if missing:
        for f in missing:
            _log(f"  LIPSESTE: {f}")
        _log("EROARE: Fisiere lipsa. Nu pot porni.")
        sys.exit(1)
    _log("  OK")

    # Step 2: Gaseste Python
    _log("Caut Python...")
    python_exe = _try_python()
    if not python_exe:
        _log("EROARE: Nu gasesc Python (nici venv, nici system).")
        sys.exit(1)
    _log(f"  {python_exe}")

    # Step 3: Verifica port
    if not _port_free(port):
        _log(f"Port {port} e ocupat. Incerc sa eliberez...")
        _kill_port(port)
        if not _port_free(port):
            # Maybe it's our own server (elevated from UAC)?
            _log("Port ocupat. Verific daca e un server ANA MAX functional...")
            ready, ready_message = _smart_readiness(timeout=5)
            if ready:
                _log(f"Server ANA MAX deja activ la http://{host}:{port}")
                _log(f"  {ready_message}")
                count = _tool_count()
                if count is not None:
                    _log(f"  Tool-uri disponibile: {count}")
                sys.exit(0)
            # Not our server, give up
            _log(f"Port {port} e ocupat de alt proces si nu poate fi oprit (posibil system/elevated).")
            _log(f"Ruleaza ca ADMINISTRATOR: taskkill /F /PID (gaseste PID cu: netstat -ano | findstr :{port})")
            sys.exit(1)
    _log(f"  Port {port} liber")

    # Step 4: Porneste serverul
    retries = state.get("retries", 0)
    attempt = 0
    while attempt <= MAX_RETRIES:
        attempt += 1
        _log(f"Pornire server (incercarea {attempt}/{MAX_RETRIES + 1})...")
        proc = start_server(python_exe, port, host, admin)
        if not proc:
            _log("EROARE: Nu am putut lansa procesul.")
            sys.exit(1)

        _log(f"  PID: {proc.pid}")

        if admin and not ctypes.windll.shell32.IsUserAnAdmin():
            # Admin mode via UAC: user must accept the dialog manually
            _log("  Astept acceptarea dialogului UAC (max 60s)...")
            ready, ready_message = _smart_readiness(timeout=60)
            if ready:
                _log("Server pornit cu succes (UAC elevation)! Health-check: OK")
                _log(f"  {ready_message}")
            else:
                _log("  Serverul nu a pornit. Ruleaza manual ca Administrator:")
                _log(f"    {python_exe} {SERVER_SCRIPT} --port {port}")
                sys.exit(1)
            state["last_ok"] = time.time()
            state["retries"] = 0
            _save_state(state)
            _log(f"\n  ANA MAX ruleaza la http://{host}:{port} (ADMIN)")
            return

        ready, ready_message = _smart_readiness(timeout=HEALTH_TIMEOUT)
        if ready:
            _log("Server pornit cu succes! Smart readiness: OK")
            _log(f"  {ready_message}")
            state["last_ok"] = time.time()
            state["retries"] = 0
            _save_state(state)

            _log(f"\n  ANA MAX ruleaza la http://{host}:{port}")
            count = _tool_count()
            if count is not None:
                _log(f"  Tool-uri disponibile: {count}")
            else:
                _log("  Tool-uri disponibile: health-check OK, count indisponibil")
            return

        _log(f"  Serverul nu raspunde. Incerc din nou...")
        _kill_port(port)
        time.sleep(3)

    # All retries exhausted
    _log("\nEROARE: Serverul nu poate porni dupa " + str(MAX_RETRIES + 1) + " incercari.")
    state["retries"] = state.get("retries", 0) + 1
    _save_state(state)
    _log("\nVerifica:")
    _log("  1. Logs: type logs\\ana_max.log")
    _log("  2. Port: netstat -ano | findstr :" + str(port))
    _log("  3. Ruleaza manual: venv\\Scripts\\python main.py --port " + str(port))
    sys.exit(1)


if __name__ == "__main__":
    main()
