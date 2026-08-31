# Architecture

`apps/web` owns the browser UI, local learning-map storage, PDF selection, and a
small Node BFF. `services/research-api` owns checked-in CC0 document ingestion,
retrieval, citation validation, and evaluation. The BFF forwards only explicit
question requests to the loopback research API; it does not forward node notes or
uploaded PDFs.

`multi-pipeline-v2` has one directional data flow:

```text
question -> Coordinator plan -> Retriever queries -> actual retrieval
         -> Solver draft -> Verifier decision -> Tutor final answer
```

Each model role has a distinct strict JSON schema. Retrieval queries are bounded
and validated before execution. Solver citations must belong to the retrieved
set; Verifier can only permit members of that set; Tutor can only use the
Verifier-permitted subset. A rejected draft cannot be revived by Tutor.

The initial question retrieval is retained only to measure how the generated
queries change the hit set. Solver receives the actual re-retrieval results, not
the initial hits. Evaluation answers and rubrics enter only after Tutor finishes.
