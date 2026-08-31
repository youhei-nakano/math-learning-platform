# Evaluation

Run deterministic checks first with `./scripts/check.sh`. Live evaluation then
progresses through easy, hard, multi-step, and unanswerable one-case smoke runs
before any 27-case run.

The version labels are:

- `single-v1`: one model call after baseline retrieval.
- `multi-fixed-v1`: historical fixed five-call records without effective query
  handoff. These records remain immutable in their original repository.
- `multi-pipeline-v2`: plan, generated queries, actual retrieval, draft,
  verification, and constrained tutoring.

Pipeline metrics include query and hit-set changes, Verifier issues, requested and
applied revisions, answer and citation differences, improvement/regression,
answerability changes, and Verifier/Tutor overhead. “Improved” is not inferred
from the existence of a Verifier; it requires post-pipeline deterministic grading
to improve. Descriptive answers still require human review.

Do not combine historical fixed-pipeline results with v2 results. Missing live
measurements are `Not run`, not zero.

## Dataset

`demo-v2` contains 27 original CC0 cases over six two-page documents: 24
answerable and three deliberately unanswerable cases, with easy, medium, and hard
items across 14 domain labels. It is a synthetic research fixture, not a claim of
coverage over real mathematical literature. The generator pins deterministic
PDF metadata and the validator checks IDs, references, pages, and dataset fields.

## Metrics

Reports distinguish answer accuracy, citation precision/recall, answerability
accuracy, completion rate, latency, tokens, and API cost. Multi-pipeline reports
also include query/hit-set changes, Verifier issue and revision rates,
Tutor-applied revisions, answer/citation changes, improved/regressed/
inconclusive classification, and revision overhead.

## Deterministic vs. live

Deterministic evaluation uses checked-in CC0 text and makes no model call. It is
appropriate for normal CI and reproducibility checks. Live evaluation is
non-deterministic, billable, explicitly opt-in, and excluded from normal CI.

The staged order is one easy, one hard, one multi-step, and one unanswerable case;
inspect trace and cost before expanding to all 27. Single and multi runs should
use the same dataset, retrieval, model family, output contract, grader, and close
execution time. Trial count and failures must be reported.

## Published state

The checked-in four-case `demo-v1` UI summary is an offline extraction smoke with
zero external model calls. It is intentionally labeled separately from live LLM
results. No complete 27-case live comparison is committed; its state is
`Not run` in the published artifacts.

## Cost controls

The live runner requires `--live`, a server-side environment key, maximum total
and per-question cost, bounded output, total token, step, retry, per-call timeout,
and per-question time limits. The manual workflow permits at most 27 cases, three
trials, 120 seconds per call, and USD 5 total. Raw JSONL is ignored; public
artifacts contain aggregate reports rather than provider response IDs.
