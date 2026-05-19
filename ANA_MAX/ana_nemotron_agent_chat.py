#!/usr/bin/env python3
"""
Chat web local pentru ANA MAX cu backend Nemotron.
Porneste o interfata de chat in browser peste ANAAgent.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template_string, request

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.chdir(BASE_DIR)

from core.config import config  # noqa: E402

config.set("ai.primary_backend", "nemotron_openrouter")
config.set("ai.routing.enabled", False)
config.set("ai.routing.backends", [])

import main as ana_main  # noqa: E402
from core.autonomous_agent import AutonomousAgent  # noqa: E402
from core.agent import ANAAgent  # noqa: E402
from core.backends import nemotron_openrouter_backend  # noqa: E402
from tools.base import registry  # noqa: E402

app = Flask(__name__)

_runtime_agent: ANAAgent | None = None
_autonomous_agent: AutonomousAgent | None = None

HTML = r"""<!doctype html>
<html lang="ro">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ANA MAX Nemotron Agent Chat</title>
  <style>
    :root {
      --bg: #f3f1eb;
      --surface: rgba(255,255,255,0.84);
      --ink: #1b201d;
      --muted: #5f655f;
      --accent: #8b3d1f;
      --accent-soft: #f1ddd1;
      --line: rgba(27,32,29,0.1);
      --shadow: 0 22px 60px rgba(28, 34, 27, 0.14);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: "Segoe UI", "Trebuchet MS", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(139,61,31,0.13), transparent 30%),
        radial-gradient(circle at bottom right, rgba(34,92,74,0.14), transparent 25%),
        linear-gradient(135deg, #f4efe8, #eef4ef 50%, #f6f1eb);
      padding: 24px;
    }
    .shell {
      max-width: 1180px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: 300px 1fr;
      gap: 18px;
    }
    .panel {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 24px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(12px);
    }
    .sidebar {
      padding: 22px;
      display: flex;
      flex-direction: column;
      gap: 18px;
    }
    .tag {
      display: inline-flex;
      padding: 8px 12px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      font-size: 13px;
      font-weight: 800;
      width: fit-content;
    }
    h1 {
      margin: 0;
      font-size: 30px;
      line-height: 1.05;
    }
    .lede {
      margin: 0;
      color: var(--muted);
      line-height: 1.5;
    }
    .card {
      padding: 14px 16px;
      border-radius: 18px;
      background: rgba(255,255,255,0.72);
      border: 1px solid var(--line);
    }
    .label {
      display: block;
      margin-bottom: 6px;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .08em;
      color: var(--muted);
    }
    .tools {
      max-height: 300px;
      overflow: auto;
      padding-left: 18px;
      margin: 10px 0 0;
      color: var(--muted);
    }
    .chat {
      display: flex;
      flex-direction: column;
      min-height: 82vh;
      overflow: hidden;
    }
    .chat-head {
      padding: 22px 24px 14px;
      border-bottom: 1px solid var(--line);
    }
    .chat-head h2 {
      margin: 0;
      font-size: 24px;
    }
    .chat-head p {
      margin: 8px 0 0;
      color: var(--muted);
    }
    .messages {
      flex: 1;
      overflow: auto;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }
    .msg {
      max-width: 86%;
      white-space: pre-wrap;
      word-break: break-word;
      line-height: 1.5;
      padding: 16px 18px;
      border-radius: 20px;
      animation: fade .2s ease;
    }
    .msg.user {
      align-self: flex-end;
      background: linear-gradient(135deg, #8b3d1f, #af5532);
      color: white;
      border-bottom-right-radius: 8px;
    }
    .msg.assistant {
      align-self: flex-start;
      background: rgba(255,255,255,0.82);
      border: 1px solid var(--line);
      border-bottom-left-radius: 8px;
    }
    .composer {
      border-top: 1px solid var(--line);
      padding: 18px 24px 24px;
      display: grid;
      gap: 12px;
    }
    textarea {
      width: 100%;
      min-height: 120px;
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
      resize: vertical;
      font: inherit;
      background: rgba(255,255,255,0.9);
      color: var(--ink);
    }
    .row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }
    .status {
      font-size: 13px;
      color: var(--muted);
    }
    button {
      border: 0;
      border-radius: 14px;
      padding: 12px 18px;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }
    .primary {
      color: white;
      background: var(--accent);
      box-shadow: 0 12px 28px rgba(139,61,31,0.22);
    }
    .ghost {
      background: rgba(27,32,29,0.08);
      color: var(--ink);
    }
    @keyframes fade {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @media (max-width: 940px) {
      .shell { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside class="panel sidebar">
      <div class="tag">Agent mode</div>
      <h1>ANA + Nemotron</h1>
      <p class="lede">Interfata de chat pentru ANA MAX cu backend Nemotron si infrastructura de tool-uri incarcata.</p>

      <div class="card">
        <span class="label">Backend</span>
        <strong id="backendLabel">se incarca...</strong>
      </div>
      <div class="card">
        <span class="label">Model</span>
        <strong id="modelLabel">se incarca...</strong>
      </div>
      <div class="card">
        <span class="label">Tool-uri</span>
        <strong id="toolCountLabel">0</strong>
        <ul id="toolsList" class="tools"></ul>
      </div>
    </aside>

    <main class="panel chat">
      <div class="chat-head">
        <h2>Vorbeste cu ANA pe Nemotron</h2>
        <p>Poti cere analiza, planuri, explicatii si taskuri. Interfata ruleaza peste ANAAgent.</p>
      </div>
      <section id="messages" class="messages">
        <div class="msg assistant">Salut! Sunt gata. Scrie ce vrei sa facem si incepem.</div>
      </section>
      <form id="composer" class="composer">
        <textarea id="prompt" placeholder="Exemplu: Analizeaza proiectul si spune-mi ce fisiere trebuie modificate pentru login."></textarea>
        <div class="row">
          <div id="status" class="status">Pregatit.</div>
          <div>
            <button type="button" id="clearBtn" class="ghost">Curata</button>
            <button type="submit" id="sendBtn" class="primary">Trimite</button>
          </div>
        </div>
      </form>
    </main>
  </div>

  <script>
    const messages = document.getElementById('messages');
    const promptEl = document.getElementById('prompt');
    const statusEl = document.getElementById('status');
    const composer = document.getElementById('composer');
    const sendBtn = document.getElementById('sendBtn');
    const clearBtn = document.getElementById('clearBtn');

    function addMessage(role, text) {
      const el = document.createElement('div');
      el.className = `msg ${role}`;
      el.textContent = text;
      messages.appendChild(el);
      messages.scrollTop = messages.scrollHeight;
    }

    function setBusy(value, text) {
      sendBtn.disabled = value;
      promptEl.disabled = value;
      statusEl.textContent = text;
    }

    async function loadHealth() {
      const res = await fetch('/health');
      const data = await res.json();
      document.getElementById('backendLabel').textContent = data.backend;
      document.getElementById('modelLabel').textContent = data.model;
      document.getElementById('toolCountLabel').textContent = String(data.tools_count);
      const toolsList = document.getElementById('toolsList');
      toolsList.innerHTML = '';
      for (const tool of data.tools.slice(0, 18)) {
        const li = document.createElement('li');
        li.textContent = tool;
        toolsList.appendChild(li);
      }
    }

    composer.addEventListener('submit', async (event) => {
      event.preventDefault();
      const message = promptEl.value.trim();
      if (!message) return;

      addMessage('user', message);
      promptEl.value = '';
      setBusy(true, 'ANA proceseaza taskul...');

      try {
        const res = await fetch('/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message })
        });
        const data = await res.json();
        if (!res.ok || !data.success) {
          throw new Error(data.error || 'Eroare necunoscuta');
        }
        addMessage('assistant', data.reply);
        statusEl.textContent = 'Gata.';
      } catch (error) {
        addMessage('assistant', `Eroare: ${error.message}`);
        statusEl.textContent = 'A aparut o eroare.';
      } finally {
        setBusy(false, statusEl.textContent);
        promptEl.focus();
      }
    });

    clearBtn.addEventListener('click', () => {
      messages.innerHTML = '';
      addMessage('assistant', 'Conversatia vizuala a fost curatata. Putem continua.');
      statusEl.textContent = 'Pregatit.';
      promptEl.focus();
    });

    loadHealth().catch(() => {
      statusEl.textContent = 'Nu pot citi statusul.';
    });
  </script>
</body>
</html>
"""


def get_agent() -> ANAAgent:
    global _runtime_agent
    if _runtime_agent is None:
        _runtime_agent = ANAAgent(backend="nemotron_openrouter")
    if not hasattr(_runtime_agent, "nemotron_api_keys"):
        nemotron_openrouter_backend.init(_runtime_agent)
    _runtime_agent.nemotron_model = config.get(
        "ai.nemotron_openrouter.model",
        "nvidia/nemotron-3-super-120b-a12b:free",
    )
    return _runtime_agent


def get_autonomous_agent() -> AutonomousAgent:
    global _autonomous_agent
    if _autonomous_agent is None:
        _autonomous_agent = AutonomousAgent(get_agent())
    return _autonomous_agent


def looks_like_execution_request(message: str) -> bool:
    lowered = message.lower()
    action_terms = (
        "creeaza", "creaza", "create", "fa", "fă", "executa", "execută", "ruleaza", "rulează",
        "analizeaza", "analizează", "gaseste", "găsește", "cauta", "caută", "editeaza", "editează",
        "modifica", "modifică", "scrie", "sterge", "șterge", "delete", "porneste", "pornește",
    )
    target_terms = (
        "folder", "director", "fisier", "fișier", "proiect", "workspace", "desktop",
        "terminal", "comanda", "comandă", "tool", "tool-uri", "tools", "cod", "codebase",
    )
    return any(term in lowered for term in action_terms) and any(term in lowered for term in target_terms)


def build_execution_reply(result: dict) -> str:
    status = "succes" if result.get("success") else "partial sau esuat"
    completed = result.get("completed_steps", 0)
    total = result.get("total_steps", 0)
    output = str(result.get("output", "") or "").strip()
    if output:
        return f"Executie {status}.\nPasi completati: {completed}/{total}\n\nRezultat:\n{output}"
    return f"Executie {status}. Pasi completati: {completed}/{total}."


def bootstrap_tools() -> int:
    try:
        return ana_main._register_all_tools()
    except Exception:
        return len(registry.list_tools())


@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML)


@app.route("/health", methods=["GET"])
def health():
    tools = sorted(registry.list_tools())
    return jsonify({
        "status": "online",
        "backend": "nemotron_openrouter",
        "model": config.get("ai.nemotron_openrouter.model", "nvidia/nemotron-3-super-120b-a12b:free"),
        "tools_count": len(tools),
        "tools": tools,
    })


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    if not message:
        return jsonify({"success": False, "error": "Mesajul este gol."}), 400

    try:
        if looks_like_execution_request(message):
            result = get_autonomous_agent().execute_task(message, max_iterations=8)
            reply = build_execution_reply(result)
        else:
            agent = get_agent()
            reply = nemotron_openrouter_backend.send(agent, message)
        return jsonify({"success": True, "reply": reply})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


def main() -> int:
    # Activeaza logging centralizat
    ana_main._configure_logging(debug=True)
    bootstrap_tools()
    host = "127.0.0.1"
    port = 8797
    print(f"[ANA Nemotron Agent Chat] Server local: http://{host}:{port}")
    app.run(host=host, port=port, debug=False, use_reloader=False, threaded=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
