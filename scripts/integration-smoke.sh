#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
python_bin="$root/services/research-api/.venv/bin/python"
learning_uvicorn="$root/services/learning-map-api/.venv/bin/uvicorn"
research_port=${RESEARCH_SMOKE_PORT:-18765}
learning_port=${LEARNING_MAP_SMOKE_PORT:-18000}
web_port=${WEB_SMOKE_PORT:-14173}
(cd "$root/services/research-api" && \
  "$python_bin" research_api.py --port "$research_port") &
research_pid=$!
(cd "$root/services/learning-map-api" && \
  env -u OPENAI_API_KEY "$learning_uvicorn" math_research_assistant.app:app \
    --host 127.0.0.1 --port "$learning_port") &
learning_pid=$!
cleanup() {
  kill "$research_pid" "$learning_pid" "${web_pid:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

for _ in {1..30}; do
  curl -fsS "http://127.0.0.1:$research_port/health" >/dev/null 2>&1 && break
  sleep 0.1
done
for _ in {1..30}; do
  curl -fsS "http://127.0.0.1:$learning_port/health" >/dev/null 2>&1 && break
  sleep 0.1
done

learning_health=$(curl -fsS "http://127.0.0.1:$learning_port/health")
[[ "$learning_health" == *'"status":"ok"'* ]]
[[ "$learning_health" == *'"aiAvailable":false'* ]]

(cd "$root/apps/web" && \
  PORT="$web_port" RESEARCH_API_URL="http://127.0.0.1:$research_port" npm start) &
web_pid=$!
for _ in {1..30}; do
  curl -fsS "http://127.0.0.1:$web_port/" >/dev/null 2>&1 && break
  sleep 0.1
done

response=$(curl -fsS -X POST "http://127.0.0.1:$web_port/api/research/query" \
  -H 'Content-Type: application/json' \
  --data '{"question":"What properties define a basis?","mode":"single"}')
[[ "$response" == *'"status": "success"'* ]]
[[ "$response" == *'"citations"'* ]]
echo "Web/research API/learning-map API integration smoke: passed"
