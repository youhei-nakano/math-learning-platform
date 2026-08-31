#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
service="$root/services/research-api"
cd "$service"
exec "$service/.venv/bin/python" evaluation/live_runner.py "$@"
