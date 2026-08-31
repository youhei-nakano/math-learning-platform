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
