#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
python_bin="$root/services/research-api/.venv/bin/python"
learning_uvicorn="$root/services/learning-map-api/.venv/bin/uvicorn"
research_port=${RESEARCH_API_PORT:-8765}
learning_port=${LEARNING_MAP_API_PORT:-8000}
web_port=${WEB_DEV_PORT:-5173}
if [[ ! -x "$python_bin" || ! -x "$learning_uvicorn" ]]; then
  echo "Run ./scripts/setup.sh first." >&2
  exit 1
fi

(cd "$root/services/research-api" && \
  "$python_bin" research_api.py --port "$research_port") &
research_pid=$!
(cd "$root/services/learning-map-api" && \
  "$learning_uvicorn" math_research_assistant.app:app \
    --reload --host 127.0.0.1 --port "$learning_port") &
learning_pid=$!
trap 'kill "$research_pid" "$learning_pid" 2>/dev/null || true' EXIT INT TERM
RESEARCH_API_URL="http://127.0.0.1:$research_port" \
VITE_LEARNING_MAP_API_URL="http://127.0.0.1:$learning_port" \
  npm run dev --prefix "$root/apps/web" -- --host 127.0.0.1 --port "$web_port"
