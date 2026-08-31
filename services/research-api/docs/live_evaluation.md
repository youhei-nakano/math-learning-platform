# Paired production LLM evaluation

The production protocol compares `live-single` (one answer call) with
`live-multi` (Coordinator, Retriever, Solver, Verifier, Tutor) on all 27
`demo-v2` cases and five trials. Both conditions receive the exact same
deterministic hybrid/top-5 retrieval result. The Retriever plan is logged for
diagnostics but cannot change that evidence set.

## Frozen conditions

- model snapshot: `gpt-5.4-mini-2026-03-17`
- prompt: `live-eval-v3-shared-retrieval`
- output limit: 600 tokens per model call
- timeout: 45 seconds; one SDK attempt plus at most one runner retry
- total measured-cost ceiling: USD 3.60; per-question ceiling: USD 0.20
- pricing checked 2026-08-31: USD 0.75/M uncached input, USD 0.075/M cached
  input, USD 4.50/M output
- schedule seed: `20260831`; condition order is deterministically shuffled for
  each question/trial pair

Every record contains the dataset/PDF hashes, Git revision and dirty flag,
prompt/model/configuration, pricing source, timestamps, shared retrieval hash,
token usage, measured cost, latency, and schedule position. The JSONL is
append-only. Successful records are skipped on resume; `--retry-failed` retries
only failures without rewriting prior observations.

The cost ledger admits each API call only when a conservative upper bound based
on prompt bytes and maximum output tokens fits in the remaining budget. It then
commits the measured Responses API usage. A failure is never a zero-cost
success. The normal CI workflow has no live command and makes no paid calls.

At live-run startup the runner first uses the process `OPENAI_API_KEY`. If it is
absent on macOS, it reads generic-password service
`math-learning-platform-openai` for the current user into the runner process
only. The captured value is never printed or written to configuration/results.

## Staged execution

Run one paired case first, then hard and unanswerable smokes. `--max-new-records`
only stages the full paired schedule and is excluded from experiment identity, so
the production command resumes the exact same experiment. Use the same JSONL so
all smoke cost counts against the USD 3.60 ledger.

```zsh
./scripts/evaluate-live.sh --live --mode paired --trials 5 \
  --case-id arith-percent-001 --max-new-records 2 \
  --experiment-name production-paired-v6-gpt54mini \
  --max-total-cost-usd 3.60 \
  --output evaluation/runs/gpt54mini-paired-v6.jsonl
```

After inspecting smoke records, run or resume the production schedule:

```zsh
./scripts/evaluate-live.sh --live --mode paired --trials 5 \
  --seed 20260831 --max-total-cost-usd 3.60 \
  --experiment-name production-paired-v6-gpt54mini \
  --output evaluation/runs/gpt54mini-paired-v6.jsonl
```

Generate every public artifact from the raw JSONL:

```zsh
.venv/bin/python evaluation/analyze_paired_live.py \
  evaluation/runs/gpt54mini-paired-v6.jsonl \
  --output-dir evaluation/live-paired-v6 \
  --app-json ../../apps/web/public/live-evaluation-status.json
```

Outputs include paired JSON/CSV, all multi losses in CSV and Markdown, and a
blind review sheet plus a separate reveal key. Blank human-review columns mean
unreviewed; deterministic grading must not be described as human-verified.

## Interpretation limits

The 27 questions are locally authored fixtures. Five repetitions measure
within-protocol variability but do not establish population validity or
statistical sufficiency. Exact/normalized automated grading may be wrong for a
semantically unusual answer, and citation page matching does not itself prove
that a passage supports every claim. These cases are routed to blind review.
