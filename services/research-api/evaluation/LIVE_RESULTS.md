# Live LLM evaluation

Experiment `14d125678646d716`; 135 complete pairs.

| Condition | Runs | Accuracy | Citation P/R | Failure rate | Cost USD | p50 latency |
|---|---:|---:|---:|---:|---:|---:|
| single | 135 | 0.815 | 0.889/0.963 | 0.000 | 0.142476 | 1.648 |
| multi | 135 | 0.815 | 0.896/0.963 | 0.000 | 0.828224 | 13.909 |

Multi wins/ties/losses: 17/101/17. Human audit remains pending.

- The 27 cases are locally authored fixtures, not a representative population.
- Five repetitions quantify run variability but do not make the sample statistically sufficient.
- Deterministic grading can misclassify semantically correct or incorrect explanations; blind human review remains pending.
