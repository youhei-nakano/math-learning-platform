# Live LLM evaluation

The live runner compares one-call `live-single` with the fixed five-role
`live-multi` workflow (coordinator, retriever, solver, verifier, tutor). Retrieval
is deterministic and identical in both conditions. Expected answers, rubrics, and
required reasoning never enter model prompts.

## Safety and reproducibility

- Calls require both `--live` and `OPENAI_API_KEY`.
- The key stays in the environment and is never written to results.
- Responses are requested with `store=false` and a strict JSON schema.
- Supplied PDF excerpts are labelled untrusted and citations are restricted to
  retrieved chunk IDs.
- Defaults cap the total run at USD 5 and each question at USD 0.20. Both caps can
  only be set within those hard limits.
- Runs are append-only JSONL. Completed `(question_id, trial)` pairs are skipped;
  `--retry-failed` retries only failed pairs.
- Each call records role, latency, model response ID, prompt hash, retry count,
  token usage, and measured API cost. It does not store the complete prompt.

The default model is the pinned `gpt-5.4-mini-2026-03-17` snapshot. Pricing
metadata is checked into each result record with its source and check date. Update
it deliberately when OpenAI pricing changes; never silently reuse stale pricing.

## Commands

Start with exactly one case and inspect the resulting JSONL:

```zsh
export OPENAI_API_KEY='set this only in your shell or secret manager'
.venv/bin/python evaluation/live_runner.py \
  --live --mode live-single \
  --case-id arith-percent-001 \
  --max-total-cost-usd 0.20 \
  --output evaluation/runs/live-single.jsonl
```

After reviewing the smoke run, run either full condition. A three-trial run is
supported with `--trials 3`, subject to the same total budget. `live-multi` can use
up to five model calls per question, so run it separately and monitor cost.

```zsh
.venv/bin/python evaluation/live_runner.py --live --mode live-multi \
  --max-total-cost-usd 5.00 --output evaluation/runs/live-multi.jsonl
```

Aggregate only measured live records:

```zsh
.venv/bin/python evaluation/report_live.py \
  evaluation/runs/live-single.jsonl evaluation/runs/live-multi.jsonl \
  --json evaluation/live-results.json \
  --csv evaluation/live-results.csv \
  --markdown evaluation/LIVE_RESULTS.md \
  --app-json /path/to/my-app/public/live-evaluation-status.json
```

The manual GitHub Actions workflow requires an environment named
`live-evaluation`, an environment secret named `OPENAI_API_KEY`, and reviewer
approval configured in repository settings. Normal CI never makes API calls.

## Interpretation

Deterministic fixture runs and live-LLM runs are different experiment families
and must not be pooled. Exact-answer grading is conservative and cannot establish
mathematical correctness of explanations. Failures remain failures, not zero-cost
successes. Missing live records are reported as **Not run**, never as zero.
