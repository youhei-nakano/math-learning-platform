#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
python_bin="$root/services/research-api/.venv/bin/python"
ruff_bin="$root/services/research-api/.venv/bin/ruff"
learning_python="$root/services/learning-map-api/.venv/bin/python"
learning_ruff="$root/services/learning-map-api/.venv/bin/ruff"

(cd "$root/services/research-api" && \
  "$ruff_bin" check . && \
  "$ruff_bin" format --check . && \
  "$python_bin" -m unittest discover -s tests -v && \
  "$python_bin" evaluation/validate_dataset.py evaluation/datasets/demo-v2/dataset.json)
(cd "$root/services/learning-map-api" && \
  "$learning_ruff" check . && \
  "$learning_ruff" format --check . && \
  "$learning_python" -m pytest)
npm run lint --prefix "$root/apps/web"
npm test --prefix "$root/apps/web"
npm run build --prefix "$root/apps/web"
"$root/scripts/integration-smoke.sh"
