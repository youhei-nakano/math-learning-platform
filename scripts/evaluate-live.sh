#!/bin/zsh
set -euo pipefail

root=${0:A:h:h}
service="$root/services/research-api"
cd "$service"
exec "$service/.venv/bin/python" evaluation/live_runner.py "$@"
