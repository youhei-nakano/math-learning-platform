# Architecture

This repository runs locally as three processes. It is not a public hosted demo.

`apps/web` owns the browser UI, local learning-map storage, PDF selection, and a
small Node BFF. `services/research-api` owns checked-in CC0 document ingestion,
retrieval, citation validation, and evaluation. The BFF forwards only explicit
question requests to the loopback research API; it does not forward node notes or
uploaded PDFs.

`services/learning-map-api` is a separate FastAPI boundary for AI learning-map
generation. The browser performs PDF parsing and sends only explicitly consented
metadata or selected page-numbered excerpts directly to the loopback service.
The PDF binary and node notes never cross this boundary. Separating its virtual
environment from `research-api` prevents evaluation dependencies from becoming a
runtime requirement of the Web product.

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

## Search and citation flow

The Web panel sends an explicit question and selected mode to its same-origin
Node BFF. The BFF applies a request-size limit, bounded timeout, and normalized
errors before forwarding to `research-api`. Retrieval returns stable document,
version, page, and chunk identifiers. Final citations are intersected with the
actually retrieved set; an unknown ID is rejected rather than displayed.

Checked-in retrieval uses only original CC0 fixtures. User PDFs are not added to
the research corpus by the Web application.

## Learning-map generation flow

1. PDF metadata, text extraction, and outline resolution run in the browser.
2. The user chooses a learning goal.
3. A first consent sends metadata, outline, and goal for section selection.
4. The user reviews the proposed section/page ranges.
5. A second consent allows only those page-numbered excerpts to be sent.
6. The learning-map API requests a strict structured graph and validates IDs,
   cycles, goal count, edge confirmation state, external prerequisites, and
   citations against the supplied pages.
7. Nodes and edges remain separately unconfirmed until human review.

An AI citation to an unsupplied page is never converted into PDF evidence. A
non-goal node left without evidence becomes an excluded external-prerequisite
suggestion; an unsupported goal and an out-of-range page remain hard errors.

## Trace and versioning

Each `multi-pipeline-v2` step records role, start time, duration, input hash,
bounded structured output, model, token/cost usage, status, and a sanitized error
code. Complete prompts, Authorization headers, API keys, and evaluation answers
are not trace fields. Historical fixed-call records are labeled
`multi-fixed-v1`; they must not be aggregated with `multi-pipeline-v2`.
