"""Check live MCP tools/list against local permission manifest.

Read-only. Exits 0 when live tools match the local manifest, exits 1 when the
running MCP process is stale or otherwise drifted.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


DEFAULT_MCP_URL = "http://127.0.0.1:8766/mcp"
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import ana_operator_status


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check live MCP tool surface drift.")
    parser.add_argument("--mcp-url", default=DEFAULT_MCP_URL)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    surface = ana_operator_status.live_tool_surface(args.mcp_url)
    surface["schema"] = "ana.live_tool_surface_check.v1"
    surface["next_action"] = (
        "Live MCP tools/list matches the local permission manifest."
        if surface.get("status") == "PASS"
        else "Restart ANA MCP so live tools/list matches the local permission manifest."
    )
    if args.json:
        print(json.dumps(surface, indent=2, ensure_ascii=False))
    else:
        print(
            "ANA Live Tool Surface: "
            f"{ana_operator_status.format_tool_surface(surface)}"
        )
        if surface.get("extra_live"):
            print("extra_live=" + ", ".join(surface["extra_live"]))
        if surface.get("missing_live"):
            print("missing_live=" + ", ".join(surface["missing_live"]))
        print(f"next_action={surface['next_action']}")
    return 0 if surface.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
