#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
python_bin="$root/services/research-api/.venv/bin/python"
(cd "$root/services/research-api" && "$python_bin" research_api.py) &
api_pid=$!
cleanup() {
  kill "$api_pid" "${web_pid:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

for _ in {1..30}; do
  curl -fsS http://127.0.0.1:8765/health >/dev/null 2>&1 && break
  sleep 0.1
done

(cd "$root/apps/web" && npm start) &
web_pid=$!
for _ in {1..30}; do
  curl -fsS http://127.0.0.1:4173/ >/dev/null 2>&1 && break
  sleep 0.1
done

response=$(curl -fsS -X POST http://127.0.0.1:4173/api/research/query \
  -H 'Content-Type: application/json' \
  --data '{"question":"What properties define a basis?","mode":"single"}')
[[ "$response" == *'"status": "success"'* ]]
[[ "$response" == *'"citations"'* ]]
echo "BFF/API integration smoke: passed"
