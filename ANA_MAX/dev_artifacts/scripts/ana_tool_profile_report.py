"""Generate a readable ANA tool profile report from permission_manifest."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
ANA_ROOT = REPO_ROOT / "ANA_MAX"
MANIFEST_PATH = ANA_ROOT / "config" / "permission_manifest.json"
REPORT_DIR = ANA_ROOT / "dev_artifacts" / "reports"
MEMORY_DIR = ANA_ROOT / "memory" / "tool_profiles"


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def tool_profiles(config: dict[str, Any]) -> list[str]:
    profiles = config.get("profiles")
    if isinstance(profiles, list) and profiles:
        return [str(item) for item in profiles]
    profile = config.get("profile")
    return [str(profile)] if profile else []


def build_report(manifest: dict[str, Any]) -> dict[str, Any]:
    tools = manifest.get("tools", {})
    if not isinstance(tools, dict):
        tools = {}
    active_profiles = manifest.get("global_settings", {}).get("active_profiles", [])
    if not isinstance(active_profiles, list):
        active_profiles = []
    active_set = {str(item) for item in active_profiles}

    profile_counts: Counter[str] = Counter()
    tier_counts: Counter[str] = Counter()
    confirmation_count = 0
    readonly_count = 0
    inactive_tools: list[str] = []
    unprofiled_tools: list[str] = []
    rows: list[dict[str, Any]] = []
    by_profile: dict[str, list[str]] = defaultdict(list)

    for tool_name, config in sorted(tools.items()):
        if not isinstance(config, dict):
            config = {}
        profiles = tool_profiles(config)
        if not profiles:
            unprofiled_tools.append(tool_name)
        for profile in profiles:
            profile_counts[profile] += 1
            by_profile[profile].append(tool_name)
        tier = str(config.get("tier") or "unknown")
        tier_counts[tier] += 1
        requires_confirmation = bool(config.get("requires_confirmation"))
        readonly = bool(config.get("readonly"))
        allowed = config.get("allowed") is not False
        if requires_confirmation:
            confirmation_count += 1
        if readonly:
            readonly_count += 1
        active = bool(profiles and set(profiles).intersection(active_set))
        if not active:
            inactive_tools.append(tool_name)
        rows.append({
            "tool": tool_name,
            "tier": tier,
            "profiles": profiles,
            "active": active,
            "readonly": readonly,
            "requires_confirmation": requires_confirmation,
            "allowed": allowed,
        })

    return {
        "schema": "ana.tool_profile_report.v1",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "manifest": str(MANIFEST_PATH),
        "summary": {
            "tools_total": len(tools),
            "active_profiles": sorted(active_set),
            "profile_counts": dict(sorted(profile_counts.items())),
            "tier_counts": dict(sorted(tier_counts.items())),
            "readonly_tools": readonly_count,
            "confirmation_required_tools": confirmation_count,
            "inactive_tools": len(inactive_tools),
            "unprofiled_tools": len(unprofiled_tools),
        },
        "inactive_tools": inactive_tools,
        "unprofiled_tools": unprofiled_tools,
        "by_profile": {key: sorted(value) for key, value in sorted(by_profile.items())},
        "tools": rows,
    }


def markdown_report(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# ANA Tool Profile Report",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Tools total: {summary['tools_total']}",
        f"- Active profiles: {', '.join(summary['active_profiles']) or 'none'}",
        f"- Read-only tools: {summary['readonly_tools']}",
        f"- Confirmation-required tools: {summary['confirmation_required_tools']}",
        f"- Inactive tools: {summary['inactive_tools']}",
        f"- Unprofiled tools: {summary['unprofiled_tools']}",
        "",
        "## Profile Counts",
        "",
    ]
    for profile, count in summary["profile_counts"].items():
        lines.append(f"- `{profile}`: {count}")
    lines.extend(["", "## Tier Counts", ""])
    for tier, count in summary["tier_counts"].items():
        lines.append(f"- `{tier}`: {count}")

    lines.extend([
        "",
        "## Tools",
        "",
        "| Tool | Tier | Profiles | Active | Read-only | Confirm | Allowed |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ])
    for row in report["tools"]:
        profiles = ", ".join(f"`{item}`" for item in row["profiles"]) or "none"
        lines.append(
            f"| `{row['tool']}` | `{row['tier']}` | {profiles} | "
            f"{yes_no(row['active'])} | {yes_no(row['readonly'])} | "
            f"{yes_no(row['requires_confirmation'])} | {yes_no(row['allowed'])} |"
        )

    if report["inactive_tools"]:
        lines.extend(["", "## Inactive Tools", ""])
        for tool in report["inactive_tools"]:
            lines.append(f"- `{tool}`")
    if report["unprofiled_tools"]:
        lines.extend(["", "## Unprofiled Tools", ""])
        for tool in report["unprofiled_tools"]:
            lines.append(f"- `{tool}`")
    return "\n".join(lines) + "\n"


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def write_outputs(report: dict[str, Any]) -> dict[str, str]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = REPORT_DIR / f"tool_profile_report_{stamp}.json"
    md_path = MEMORY_DIR / "TOOL_PROFILE_REPORT.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(markdown_report(report), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def print_human(report: dict[str, Any], outputs: dict[str, str] | None = None) -> None:
    summary = report["summary"]
    print(
        "ANA Tool Profiles: "
        f"tools={summary['tools_total']} profiles={summary['profile_counts']} "
        f"confirm={summary['confirmation_required_tools']} inactive={summary['inactive_tools']} "
        f"unprofiled={summary['unprofiled_tools']}"
    )
    if outputs:
        print(f"json={outputs['json']}")
        print(f"markdown={outputs['markdown']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate ANA tool profile report.")
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    parser.add_argument("--no-write", action="store_true", help="Do not write report files.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(load_manifest())
    outputs = None if args.no_write else write_outputs(report)
    if args.json:
        print(json.dumps({**report, "outputs": outputs}, indent=2, ensure_ascii=False))
    else:
        print_human(report, outputs)
    return 0 if report["summary"]["unprofiled_tools"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
