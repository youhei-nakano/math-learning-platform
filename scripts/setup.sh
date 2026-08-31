#!/bin/zsh
set -euo pipefail

root=${0:A:h:h}
python3 -m venv "$root/services/research-api/.venv"
"$root/services/research-api/.venv/bin/pip" install \
  -r "$root/services/research-api/requirements.txt" \
  -r "$root/services/research-api/requirements-dev.txt"
npm ci --prefix "$root/apps/web"
