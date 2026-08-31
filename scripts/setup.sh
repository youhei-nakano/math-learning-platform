#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
python3 -m venv "$root/services/research-api/.venv"
"$root/services/research-api/.venv/bin/pip" install \
  -r "$root/services/research-api/requirements.txt" \
  -r "$root/services/research-api/requirements-dev.txt"
python3 -m venv "$root/services/learning-map-api/.venv"
"$root/services/learning-map-api/.venv/bin/pip" install \
  -e "$root/services/learning-map-api[dev]"
npm ci --prefix "$root/apps/web"
