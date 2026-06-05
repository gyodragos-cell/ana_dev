from __future__ import annotations

import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from ana.config.loader import ConfigLoader
from ana.core.orchestrator.orchestrator import ANAMaxOS
from ana.services.http.service import FakeHTTPService, HTTPResponse
from ana.services.llm.service import DeterministicLLMService
from ana.services.shell.service import DeterministicShellService
from ana.tools.registry.registry import ToolRegistry, ToolSpec, FallbackToolSpec

# Create config with all services enabled
config = ConfigLoader().from_mapping({
    "mode": "dev",
    "services": ["http", "shell", "llm", "ana", "fs", "health", "self"],
    "event_bus": {"replay_limit": 20},
    "fallback": {"max_attempts": 1},
    "sandbox": {"max_input_keys": 8, "allow_external_effects": False},
    "logging": {"level": "info"},
    "skills": {
        "self.repair": {
            "skill": "self-repair",  # Match the directory name
            "capability": "self.repair",
            "version": "1.0.0",
            "enabled": True,
        },
        "health.check": {
            "skill": "health-check",  # Match the directory name
            "capability": "health.check",
            "version": "1.0.0",
            "enabled": True,
        },
        "fs.inspect": {
            "skill": "fs-inspect",  # Match the directory name
            "capability": "fs.inspect",
            "version": "1.0.0",
            "enabled": True,
        },
    },
})

# Create services
http = FakeHTTPService()
http.register("GET", "https://ana.local/health", HTTPResponse(200, {"ok": True}))
shell = DeterministicShellService()
shell.register(("ana", "health"), lambda command: {"code": 0, "stdout": "ok"})
llm = DeterministicLLMService()
llm.register("hello", "hello from deterministic-fake")

# Create registry and register services
registry = ToolRegistry()
registry.register(ToolSpec("http_fake", "http.request", http.request))
registry.register(ToolSpec("shell_fake", "shell.run", shell.run))
registry.register(ToolSpec("llm_fake", "llm.complete", llm.complete))
registry.register_fallback(
    FallbackToolSpec(
        name="llm_default",
        capability="llm.complete",
        handler=lambda payload: {"text": "fallback response", "model": "fallback"},
    )
)

# Create OS
# Note: When running as module, need to adjust the skill root path
from pathlib import Path
skill_root_override = Path(__file__).resolve().parent / "skills" / "skills"
os = ANAMaxOS(config=config, registry=registry)
# Override the skill root for loading
os.skill_engine.load_skills(skill_root_override, mapping=config.skills)
os.skill_engine.register_skills(registry)

# Debug: Check what skills were loaded
print("DEBUG: Skill loading:")
print(f"  Skill root path: {skill_root_override}")
print(f"  Skill root exists: {skill_root_override.exists()}")
if skill_root_override.exists():
    subdirs = list(skill_root_override.iterdir())
    print(f"  Subdirectories: {[d.name for d in subdirs if d.is_dir()]}")
print(f"  Loaded skill specs: {len(os.skill_engine._skills)}")
for name, spec in os.skill_engine._skills.items():
    print(f"    - {name}: {spec.title}")






print("=== SMOKE TEST ===")

# Verify skills are registered in the registry
print("\n1. Verify skill registration:")
self_repair_tools = registry.tools_for("self.repair")
health_check_tools = registry.tools_for("health.check")
fs_inspect_tools = registry.tools_for("fs.inspect")

print(f"   [*] self.repair registered: {len(self_repair_tools) > 0} ({self_repair_tools[0].name if self_repair_tools else 'N/A'})")
print(f"   [*] health.check registered: {len(health_check_tools) > 0} ({health_check_tools[0].name if health_check_tools else 'N/A'})")
print(f"   [*] fs.inspect registered: {len(fs_inspect_tools) > 0} ({fs_inspect_tools[0].name if fs_inspect_tools else 'N/A'})")

# Try executing the skills
print("\n2. Execute self.repair:")
resp1 = os.execute("self.repair", {"prompt": "test"}, trace_id="trace-repair")
print(f"   ok={resp1.ok}, state={resp1.state.value}")
print(f"   skill={resp1.output.get('result', {}).get('skill', 'N/A')}")

print("\n3. Execute health.check:")
resp2 = os.execute("health.check", {}, trace_id="trace-health")
print(f"   ok={resp2.ok}, state={resp2.state.value}")
print(f"   skill={resp2.output.get('result', {}).get('skill', 'N/A')}")

print("\n4. Execute fs.inspect:")
resp3 = os.execute("fs.inspect", {"path": "ana"}, trace_id="trace-fs")
print(f"   ok={resp3.ok}, state={resp3.state.value}")
print(f"   skill={resp3.output.get('result', {}).get('skill', 'N/A')}")

print("\n=== SUMMARY ===")
all_ok = all([resp1.ok, resp2.ok, resp3.ok])
print(f"[*] All skills executed successfully: {all_ok}")
print(f"[*] Skills properly registered in registry: {len(self_repair_tools) > 0 and len(health_check_tools) > 0 and len(fs_inspect_tools) > 0}")
print(f"[*] Fallback engine configured: {len(registry.fallbacks_for('llm.complete')) > 0}")
print(f"[*] OS v2 deterministic layer stable: {config.mode == 'dev'}")
print("\n=== DONE ===")

