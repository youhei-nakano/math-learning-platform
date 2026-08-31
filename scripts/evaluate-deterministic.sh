#!/usr/bin/env bash
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
service="$root/services/research-api"
python_bin="$service/.venv/bin/python"
output=${1:-/tmp/math-learning-deterministic.jsonl}
single_output=${output%.jsonl}-single.jsonl
multi_output=${output%.jsonl}-multi.jsonl

(cd "$service" && "$python_bin" evaluation/run_research.py \
  --dataset evaluation/datasets/demo-v1/dataset.json \
  --config evaluation/configs/single-hybrid-rerank.json \
  --output "$single_output" --no-resume)
(cd "$service" && "$python_bin" evaluation/run_research.py \
  --dataset evaluation/datasets/demo-v1/dataset.json \
  --config evaluation/configs/multi-hybrid-rerank.json \
  --output "$multi_output" --no-resume)

"$python_bin" - "$single_output" "$multi_output" <<'PY'
import json
import sys
from pathlib import Path

for name in sys.argv[1:]:
    rows = [json.loads(line) for line in Path(name).read_text().splitlines() if line]
    if len(rows) != 4 or any(
        row["status"] != "success"
        or not row["answer_correct"]
        or row["citation_precision"] != 1.0
        or row["citation_recall"] != 1.0
        for row in rows
    ):
        raise SystemExit(f"deterministic evaluation failed: {name}")
    print(f"verified {name}: 4/4 answers and citations")
PY
