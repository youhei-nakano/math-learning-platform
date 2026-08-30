# Research architecture

```text
my-app (React, local learning maps and node notes)
  | explicit, future API boundary; node notes are not sent by default
  v
research_platform (offline-first experiment core)
  ingest -> chunk/version -> keyword|local-vector|hybrid -> optional rerank
  -> single OR coordinator/retriever/solver-tutor/verifier -> citation check
  -> resumable JSONL -> CSV/Markdown
```

The existing `math-research-assistant-portfolio` FastAPI remains the AI graph
backend. `openai-sandbox` is not silently connected to `my-app`. A future
adapter must require explicit user intent and send only the selected question,
document IDs, and selected node context; node notes remain local unless the user
explicitly includes them.

## Agent contracts

| Agent | Input | Output | Tools | Stops/failure |
|---|---|---|---|---|
| Coordinator | question, limits | bounded plan | none | one plan; fail at max steps |
| Retriever | query, approved index | scored chunk IDs | search/get chunk | timeout or no evidence |
| Solver-Tutor | question, evidence | evidence-only explanation | deterministic math tools | no unsupported claims |
| Verifier | answer, retrieved IDs | citation verdict | citation validator | rejects fabricated citations |

The offline multi mode has four bounded steps. Production model adapters must
also enforce total timeout, retry, token, and cost limits from
`ExperimentConfig`. Retrieved text is evidence, never instructions.

## Function calling vs MCP

Function calling is the default for fixed in-process operations because it is
easier to validate and test. MCP remains appropriate for reusable deterministic
tools across clients; the existing guarded differentiation server is retained.
Read-only `search_documents`, `get_chunk`, and `verify_citations` are specified.
PDF ingestion, node writes, and experiment execution are deliberately not
model-callable until authorization, idempotency keys, and audit storage exist.
