#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

if [ -d ".venv" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

python ANA_MAX/dev_artifacts/scripts/ana_linux_readiness.py --no-write

python -m pytest \
  tests/runtime/test_ana_linux_readiness.py \
  tests/runtime/test_ana_autonomy_runner.py \
  tests/runtime/test_ana_code_map.py \
  tests/runtime/test_ana_graph_map.py \
  tests/runtime/test_code_context_pack_tool.py \
  tests/runtime/test_graph_context_pack_tool.py \
  tests/runtime/test_session_audit_tool.py \
  tests/runtime/test_tool_router_tool.py \
  -q

echo "[ANA Linux] core gate passed"
