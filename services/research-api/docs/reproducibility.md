# Reproducing experiments

1. Create the virtual environment and install requirements.
2. Rebuild CC0 fixtures with `python evaluation/datasets/demo-v1/generate_fixtures.py`.
3. Verify SHA-256 values in `dataset.json`.
4. Run each config with `python evaluation/run_research.py --config ... --output ...jsonl`.
5. Generate CSV and Markdown with `evaluation/report_research.py`.

JSONL is append-only and completed case IDs are skipped on resume. Every row
stores experiment ID, full config, dataset version, Git revision, latency,
status, answer, citations, tool calls, usage fields, and error category. Offline
usage and cost are zero; unavailable token counts are `null`, never estimated.
External API runs must use a distinct output directory and must not overwrite
offline results.
