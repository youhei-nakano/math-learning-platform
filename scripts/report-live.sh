#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
service="$root/services/research-api"
cd "$service"
if [[ $# -ne 1 ]]; then
  echo "usage: $0 RAW_JSONL" >&2
  exit 2
fi
exec "$service/.venv/bin/python" evaluation/analyze_paired_live.py "$1" \
  --output-dir evaluation/live-paired \
  --app-json "$root/apps/web/public/live-evaluation-status.json"
