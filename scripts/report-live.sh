#!/bin/zsh
set -euo pipefail

root=${0:A:h:h}
service="$root/services/research-api"
cd "$service"
exec "$service/.venv/bin/python" evaluation/report_live.py "$@" \
  --json evaluation/live-results.json \
  --csv evaluation/live-results.csv \
  --markdown evaluation/LIVE_RESULTS.md \
  --app-json "$root/apps/web/public/live-evaluation-status.json"
