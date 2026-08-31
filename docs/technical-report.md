# Does a Multi-Agent Pipeline Improve Grounded Mathematics Assistance?

## A Paired Production Evaluation of Quality, Cost, Latency, and Failure Modes

**Technical report · 1 September 2026**  
**Repository:** Math Learning Platform  
**Experiment:** `14d125678646d716`

## Abstract

This report evaluates whether decomposing a grounded mathematics assistant into
multiple language-model roles improves its answers enough to justify the added
operational cost. We compare a single-call baseline with a five-stage pipeline
(Coordinator, Retriever, Solver, Verifier, and Tutor) on 27 locally authored,
CC0-licensed cases repeated five times. The comparison is paired: both
conditions use the same `gpt-5.4-mini-2026-03-17` snapshot, the same question,
and the exact same deterministic hybrid/top-5 retrieval output. All 135 pairs
completed successfully.

The two conditions produced identical aggregate answer accuracy (81.5%; 110 of
135 runs each). The multi-agent pipeline improved answerability classification
by 3.0 percentage points and citation precision by 0.7 points, but neither
change translated into higher answer accuracy. It cost 5.8 times as much and
increased median latency from 1.65 to 13.91 seconds (8.4 times). Pair outcomes
were symmetric: multi-agent won 17, tied 101, and lost 17. The verifier detected
issues, but some remained unfixed, and three downstream revisions converted an
otherwise correct answer into an incorrect one. Under this protocol, the
evidence supports retaining the single-call system as the default and treating
multi-agent orchestration as a targeted intervention rather than a universal
upgrade.

## 1. Research question and contribution

The central research question is:

> When retrieval evidence and model capability are held constant, does a
> role-separated multi-agent workflow improve grounded mathematics answers
> enough to compensate for its additional cost, latency, and failure surface?

This question matters because agent decomposition can appear more rigorous by
construction: one role plans, another retrieves, a solver answers, a verifier
checks, and a tutor revises. Architectural sophistication, however, is not an
outcome measure. Each additional call can add useful deliberation, but it can
also propagate mistakes, dilute evidence constraints, or overwrite a correct
intermediate answer.

The main contribution is a controlled production comparison that removes a
common confound. Retrieval is shared rather than independently selected by each
condition. The experiment therefore tests orchestration—not whether one system
happened to receive better evidence. It also records answer quality, citations,
answerability, latency, token usage, measured API cost, verifier behavior, and
downstream regressions at the paired-run level.

## 2. Hypotheses

Four hypotheses were specified for interpretation:

- **H1 — quality:** the multi-agent pipeline will improve answer accuracy by
  decomposing planning, solving, verification, and revision.
- **H2 — grounding:** explicit retrieval and verification roles will improve
  citation precision or recall and rejection of unanswerable questions.
- **H3 — overhead:** multiple sequential model calls will increase latency,
  token use, and API cost.
- **H4 — revision risk:** verification will sometimes repair errors, but the
  longer pipeline can also introduce downstream regressions.

The results reject H1 for this evaluation, weakly support H2, strongly support
H3, and provide direct evidence for both sides of H4.

## 3. Related work

Retrieval-augmented generation (RAG) combines parametric generation with
external evidence, addressing provenance and knowledge-access limitations in
purely parametric models [1]. This project adopts the same broad grounding
motivation but focuses on a local mathematics corpus, explicit citations, and a
controlled orchestration comparison rather than training a retriever-generator
model.

Chain-of-thought research showed that intermediate reasoning can improve some
arithmetic, symbolic, and commonsense tasks [2]. ReAct extended this direction
by interleaving reasoning with actions against external environments [3]. These
results motivate structured inference, but they do not imply that more stages
or more model calls always improve a fixed application.

Multi-agent frameworks such as AutoGen make role-based conversational workflows
programmable and demonstrate their applicability across domains including
mathematics and question answering [4]. The present study asks a narrower
engineering question: for a bounded, evidence-grounded mathematics assistant,
does one concrete five-role pipeline outperform a strong single-call baseline
when model and evidence are controlled? The answer in this dataset is no on
aggregate accuracy, despite localized benefits.

## 4. System and experimental design

### 4.1 Conditions

The **single** condition makes one model call to produce the grounded answer.
The **multi** condition executes five roles:

1. **Coordinator:** classifies the task and produces a bounded plan.
2. **Retriever:** proposes diagnostic retrieval queries.
3. **Solver:** constructs an answer from the supplied evidence.
4. **Verifier:** checks correctness, citation validity, support, and
   answerability.
5. **Tutor:** returns the final answer and may apply requested revisions.

The Retriever's proposed queries are logged for diagnostics but cannot alter the
evidence used in the comparison. Both conditions receive the exact same
deterministic hybrid/top-5 results. This prevents retrieval variance from being
mistaken for an orchestration effect.

### 4.2 Dataset and repetition

The `demo-v2` dataset contains 27 original CC0 cases: 24 answerable questions
and three deliberately unanswerable questions, spanning 14 domain labels. Each
case is run five times in each condition, producing 135 complete pairs and 270
condition-level observations. Repetition captures within-protocol stochastic
variation; it does not turn 27 authored questions into a representative sample
of mathematics learning tasks.

### 4.3 Frozen configuration

| Item | Value |
|---|---|
| Model snapshot | `gpt-5.4-mini-2026-03-17` |
| Dataset | `demo-v2` |
| Prompt version | `live-eval-v3-shared-retrieval` |
| Retrieval | deterministic hybrid, top 5, shared by both conditions |
| Trials | 5 per case and condition |
| Output limit | 600 tokens per model call |
| Timeout and retries | 45 seconds; at most one runner retry |
| Schedule | paired order deterministically shuffled; seed `20260831` |
| Grader | `deterministic-v4` |

The append-only JSONL records dataset and document hashes, implementation hash,
Git revision and dirty state, prompt and model configuration, pricing, token
usage, latency, retrieval hash, and schedule position. Budget admission uses a
conservative pre-call estimate; failures are never represented as zero-cost
successes.

### 4.4 Measures

The primary measure is deterministic answer correctness. Secondary measures are
citation precision and recall, answerability accuracy, terminal failure rate,
latency, token usage, and measured API cost. Paired mean differences and 95%
bootstrap intervals are reported from the generated analysis. Failure labels
identify verifier detections, effective revisions, citation defects, and
downstream regressions. A blind human-audit worksheet was generated but has not
yet been completed.

## 5. Results

### 5.1 Aggregate outcomes

| Measure | Single call | Multi-agent | Multi minus single |
|---|---:|---:|---:|
| Answer accuracy | 81.5% | 81.5% | 0.0 pp |
| 95% interval for accuracy | 74.9–88.1% | 74.9–88.1% | −8.1 to +8.1 pp |
| Citation precision | 88.9% | 89.6% | +0.7 pp |
| Citation recall | 96.3% | 96.3% | 0.0 pp |
| Answerability accuracy | 96.3% | 99.3% | +3.0 pp |
| Terminal failure rate | 0% | 0% | 0 pp |
| Median latency | 1.648 s | 13.909 s | +12.261 s |
| Mean latency | 2.659 s | 19.326 s | +16.667 s |
| Total condition cost | $0.142476 | $0.828224 | +$0.685748 |
| Mean cost per run | $0.001055 | $0.006135 | +$0.005080 |
| Total tokens | 114,878 | 599,849 | +484,971 |

The primary outcome is a null aggregate difference: both conditions were
correct on 110 of 135 runs. The paired accuracy difference is 0.0 percentage
points, with a 95% bootstrap interval from −8.1 to +8.1 points. The interval is
too wide to claim equivalence, but the observed data provide no accuracy gain
for the multi-agent system.

Multi-agent citation precision was 0.7 points higher, while recall was
unchanged. Answerability accuracy improved from 96.3% to 99.3%; the paired
improvement was 3.0 points (95% bootstrap interval: +0.7 to +5.9 points). This
localized benefit is relevant for abstention behavior, but it did not raise the
overall answer-correctness score.

### 5.2 Efficiency

The multi-agent condition used 599,849 tokens versus 114,878, a 5.2-fold
increase. Its measured condition cost was 5.8 times higher. Median latency rose
8.4-fold, and mean latency increased by 16.67 seconds per run (95% bootstrap
interval: +14.69 to +18.78 seconds). Thus H3 is not merely directionally
supported; overhead dominates the operational comparison.

The total recorded condition cost was $0.970700. The experiment also recorded
$0.013581 in retry overhead, which is kept separate from the condition totals
so that the primary comparison is not distorted by recovery attempts.

### 5.3 Paired wins and losses

The multi-agent pipeline won 17 pairs, tied 101, and lost 17. Ninety-three pairs
were correct in both conditions and eight were incorrect in both. The exact
symmetry of wins and losses explains the zero aggregate accuracy difference and
shows why reporting only successful examples would be misleading.

In 92 pairs, quality was equal while the multi-agent condition increased cost
or latency. This does not prove that decomposition is never useful; it shows
that unconditional use is inefficient for most cases in this workload.

## 6. Failure analysis

The verifier reported an issue in 12.6% of multi-agent runs and requested a
revision in 5.9%. Fourteen runs were labeled as verifier revision successes,
demonstrating that the extra stage sometimes repaired or improved an answer.
However, ten runs were labeled `verifier_detected_but_not_fixed`. Detection is
therefore not equivalent to correction.

Three runs (2.2%) were downstream regressions: later stages turned an otherwise
correct intermediate result into an incorrect final answer. These occurred on
integration and linear-coordinate cases in the recorded analysis. The failure
mechanism is structurally important. A pipeline can add a checker yet still
reduce reliability when revision authority is not gated by confidence,
evidence, or a demonstrated improvement criterion.

Citation behavior was also mixed. Multi-agent citation precision improved in
six pairs and worsened in seven. Some unanswerable questions exposed a mismatch
between mathematical solvability from the question and answerability under the
system's evidence-only contract. This distinction should be made explicit in
future graders and user-facing abstentions.

The practical lesson is to make revision selective. A verifier should identify
a concrete defect, cite the violated constraint, and propose a minimally scoped
change. The system should preserve the pre-revision answer and accept a rewrite
only when an independent check indicates improvement.

## 7. Limitations and validity threats

**Dataset scope.** The cases are locally authored fixtures, not a random or
representative sample of real student questions. Domain coverage is broad in
labels but shallow in examples.

**Repeated observations.** Five trials per case measure run variability, but
observations sharing a case are not equivalent to 135 independently sampled
questions. Intervals should be read as protocol-level uncertainty, not broad
population guarantees.

**Automated grading.** Exact and normalized deterministic checks can mark a
semantically valid response wrong or accept a weak explanation. Page-level
citation matching does not prove that every claim is supported. The prepared
blind human audit remains pending.

**Single model and pipeline.** Results apply to the frozen model snapshot,
prompts, roles, stopping rules, and evidence set. They do not establish that all
multi-agent systems are inefficient, nor that a targeted or parallel design
would behave similarly.

**Dirty execution state.** The run records preserve a dirty Git-state flag and
an implementation hash. This improves traceability but is weaker than executing
from a clean, signed release commit.

**Latency environment.** Wall-clock measurements include provider and network
variation from one execution environment. Cost is more directly reproducible
than latency.

## 8. Decision and next experiments

The single-call condition remains the default because it matched answer
accuracy while being substantially faster, cheaper, and simpler. Multi-agent
execution should be triggered only for cases with a testable reason to benefit,
such as low-confidence answerability decisions or defects that a verifier can
identify precisely.

The next experiments are:

1. Complete the blind human audit and report agreement between independent
   raters before making stronger semantic-quality claims.
2. Expand the dataset with externally sourced, license-compatible tasks and
   stratify results by complexity, answerability, and error type.
3. Evaluate a gated verifier that runs only on uncertain cases and cannot
   replace a correct draft without a validated reason.
4. Compare sequential role separation with cheaper alternatives: one-call
   structured prompting, selective retry, and parallel candidate generation.
5. Re-run from a clean tagged commit and publish the immutable raw record hashes.

## 9. Reproducibility artifacts

- Summary: [`services/research-api/evaluation/LIVE_RESULTS.md`](../services/research-api/evaluation/LIVE_RESULTS.md)
- Protocol: [`services/research-api/docs/live_evaluation.md`](../services/research-api/docs/live_evaluation.md)
- Paired analysis: [`services/research-api/evaluation/live-paired-v6/paired-results.json`](../services/research-api/evaluation/live-paired-v6/paired-results.json)
- All pair-level rows: [`services/research-api/evaluation/live-paired-v6/all-paired-cases.csv`](../services/research-api/evaluation/live-paired-v6/all-paired-cases.csv)
- Multi-agent loss audit: [`services/research-api/evaluation/live-paired-v6/MULTI_LOSSES.md`](../services/research-api/evaluation/live-paired-v6/MULTI_LOSSES.md)
- Blind audit sheet and separate reveal key: `blind-audit.csv` and
  `blind-audit-key.csv` in the same analysis directory

## References

1. Lewis, P. et al. (2020). [Retrieval-Augmented Generation for
   Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401). NeurIPS.
2. Wei, J. et al. (2022). [Chain-of-Thought Prompting Elicits Reasoning in Large
   Language Models](https://arxiv.org/abs/2201.11903). NeurIPS.
3. Yao, S. et al. (2023). [ReAct: Synergizing Reasoning and Acting in Language
   Models](https://arxiv.org/abs/2210.03629). ICLR.
4. Wu, Q. et al. (2024). [AutoGen: Enabling Next-Gen LLM Applications via
   Multi-Agent Conversation](https://arxiv.org/abs/2308.08155). COLM.
