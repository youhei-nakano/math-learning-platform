#!/bin/zsh
set -euo pipefail

root=${0:A:h:h}
service="$root/services/research-api"
python_bin="$service/.venv/bin/python"
output=${1:-/tmp/math-learning-deterministic.jsonl}
(cd "$service" && "$python_bin" evaluation/run_research.py \
  --dataset evaluation/datasets/demo-v2/dataset.json \
  --config evaluation/configs/single-hybrid-rerank.json \
  --output "$output" --case-id arith-percent-001 --no-resume)
