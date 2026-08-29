# Evaluation strategy

## Retrieval

`evaluation/questions.json` contains ten Japanese/English literature questions
and expected PDF pages. Retrieval succeeds when an expected page appears in the
top three results.

Current baseline: Hit@3 = 7/10 (70%). The three misses remain in the set.

## Answerability

Ten in-document questions and five out-of-document questions were compared by
maximum cosine similarity. The observed separation was:

- in-document minimum: 0.5869
- out-of-document maximum: 0.4571
- selected threshold: 0.52

This is a small-dataset threshold, not a universal constant.

## Workflow routing

`evaluation/workflow_cases.json` includes literature, differentiation,
unsupported differentiation, Japanese, and English cases. The evaluator checks
the selected tool without executing PDF retrieval or SymPy through the model.

Measured result: 6/6 correct tool selections (100%), 10.675 seconds total.

## Multi-agent comparison

The Agents SDK handoff experiment uses the same routing cases. Compare accuracy,
latency, API usage, and operational complexity against the single-router
baseline. Do not adopt multi-agent orchestration solely because it is available.

Measured result: 6/6 correct handoffs (100%), 13.685 seconds total. Because the
accuracy was unchanged and the handoff version took about 28% longer, the single
router remains the default architecture.
