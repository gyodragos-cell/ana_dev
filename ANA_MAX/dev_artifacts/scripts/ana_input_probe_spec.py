"""ANA MAX lab-only input instrumentation probe spec.

This does not run Frida or capture input. It emits a guarded diagnostic spec for
authorized local debugging where the operator needs to confirm whether a target
process calls Windows input APIs. Keep it lab-only.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone


SUPPORTED_APIS = {
    "GetAsyncKeyState": {
        "module": "user32.dll",
        "export": "GetAsyncKeyState",
        "risk": "high",
        "notes": "Called frequently. Use short duration and aggregate VK counts only.",
    },
    "GetKeyboardState": {
        "module": "user32.dll",
        "export": "GetKeyboardState",
        "risk": "high",
        "notes": "Keyboard state API. Do not store key states or text.",
    },
    "RegisterRawInputDevices": {
        "module": "user32.dll",
        "export": "RegisterRawInputDevices",
        "risk": "medium",
        "notes": "Good static/runtime signal that an app registers HID raw input.",
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_spec(target: str, api: str, duration: int, sample_limit: int) -> dict:
    duration = max(1, min(int(duration), 10))
    sample_limit = max(1, min(int(sample_limit), 200))
    item = SUPPORTED_APIS[api]
    return {
        "schema": "ana.input_probe_spec.v1",
        "generated_at": now_iso(),
        "mode": "lab-only",
        "target": target,
        "api": api,
        "module": item["module"],
        "export": item["export"],
        "risk": item["risk"],
        "duration_sec_max": duration,
        "sample_limit_max": sample_limit,
        "policy": {
            "requires_operator_confirmation": True,
            "authorized_targets_only": True,
            "no_anti_cheat_bypass": True,
            "no_continuous_monitoring": True,
            "no_raw_key_storage": True,
            "no_character_decoding": True,
            "aggregate_counts_only": True,
            "public_release": "forbidden",
        },
        "allowed_output": {
            "target_process": target,
            "api": api,
            "calls_total": "integer",
            "unique_codes_count": "integer",
            "top_codes": "list of VK integer counts, no text",
            "duration_sec": "integer",
        },
        "notes": item["notes"],
        "frida_template": build_template(api, item["module"], item["export"], sample_limit),
    }


def build_template(api: str, module: str, export: str, sample_limit: int) -> str:
    if api in {"GetAsyncKeyState", "GetKeyboardState"}:
        return f"""// ANA MAX lab-only input API probe.
// Guardrails: short duration, aggregate counts only, no character decoding.
const target = Module.findExportByName("{module}", "{export}");
const counts = {{}};
let callsTotal = 0;
const sampleLimit = {sample_limit};

Interceptor.attach(target, {{
  onEnter(args) {{
    callsTotal += 1;
    if (callsTotal > sampleLimit) return;
    const code = args[0].toInt32();
    counts[code] = (counts[code] || 0) + 1;
  }}
}});

setTimeout(function () {{
  send({{
    type: "ana_input_probe_summary",
    api: "{api}",
    calls_total: callsTotal,
    unique_codes_count: Object.keys(counts).length,
    top_codes: Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 10)
  }});
}}, 5000);
"""
    return f"""// ANA MAX lab-only Raw Input registration probe.
const target = Module.findExportByName("{module}", "{export}");
let callsTotal = 0;

Interceptor.attach(target, {{
  onEnter(args) {{
    callsTotal += 1;
  }}
}});

setTimeout(function () {{
  send({{
    type: "ana_input_probe_summary",
    api: "{api}",
    calls_total: callsTotal
  }});
}}, 5000);
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate lab-only ANA input instrumentation probe spec.")
    parser.add_argument("--target", required=True, help="Authorized local target process name or PID.")
    parser.add_argument("--api", choices=sorted(SUPPORTED_APIS), default="RegisterRawInputDevices")
    parser.add_argument("--duration", type=int, default=5)
    parser.add_argument("--sample-limit", type=int, default=100)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print(json.dumps(build_spec(args.target, args.api, args.duration, args.sample_limit), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
