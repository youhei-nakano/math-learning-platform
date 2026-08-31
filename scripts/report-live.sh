#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
service="$root/services/research-api"
cd "$service"
exec "$service/.venv/bin/python" evaluation/report_live.py "$@" \
  --json evaluation/live-results.json \
  --csv evaluation/live-results.csv \
  --markdown evaluation/LIVE_RESULTS.md \
  --app-json "$root/apps/web/public/live-evaluation-status.json"
