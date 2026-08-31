#!/bin/zsh
set -euo pipefail

root=${0:A:h:h}
python_bin="$root/services/research-api/.venv/bin/python"
if [[ ! -x "$python_bin" ]]; then
  echo "Run ./scripts/setup.sh first." >&2
  exit 1
fi

(cd "$root/services/research-api" && "$python_bin" research_api.py) &
api_pid=$!
trap 'kill "$api_pid" 2>/dev/null || true' EXIT INT TERM
npm run dev --prefix "$root/apps/web"
