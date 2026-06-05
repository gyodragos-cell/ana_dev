#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

echo "[ANA Linux] root=$ROOT"
echo "[ANA Linux] Python: $(python3 --version 2>/dev/null || python --version)"

PYTHON_BIN="python3"
if ! command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

if [ ! -d ".venv" ]; then
  echo "[ANA Linux] creating .venv"
  "$PYTHON_BIN" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip

if [ -f "ANA_MAX/requirements.txt" ]; then
  echo "[ANA Linux] installing ANA_MAX/requirements.txt"
  python -m pip install -r ANA_MAX/requirements.txt
fi

echo "[ANA Linux] installing lightweight dev test tools"
python -m pip install pytest

echo "[ANA Linux] static readiness"
python ANA_MAX/dev_artifacts/scripts/ana_linux_readiness.py --no-write

echo "[ANA Linux] core compile"
python -m compileall -q \
  ANA_MAX/main.py \
  ANA_MAX/tools \
  ANA_MAX/dev_artifacts/scripts/ana_linux_readiness.py \
  ANA_MAX/dev_artifacts/scripts/ana_autonomy_runner.py \
  ANA_MAX/dev_artifacts/scripts/ana_nucleus_smoke.py \
  ANA_MAX/dev_artifacts/scripts/ana_code_map.py \
  ANA_MAX/dev_artifacts/scripts/ana_graph_map.py

echo "[ANA Linux] bootstrap complete"
