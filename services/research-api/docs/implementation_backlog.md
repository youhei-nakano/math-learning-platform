# Executable backlog

1. **Neural retrieval adapter** - Input: versioned chunks/query; output: scored
   chunk IDs with model/version/usage. Done when mocked and live-gated tests pass
   and hybrid ablation runs without answer leakage. Depends on API approval.
2. **OCR adapter** - Input: explicit PDF page; output: text, confidence spans,
   page identity, latency/cost. Done when scanned bilingual fixtures pass and
   failures never become empty success. Depends on OCR engine/license review.
3. **VLM adapter** - Input: explicit page image and purpose; output: provisional
   structured observations with provenance. Done when diagram fixtures and
   failure/cost tests pass. Depends on user consent and API approval.
4. **Authorized application API** - Input: selected document/question/node ID,
   optional explicitly selected memo; output: cited response. Done when CORS,
   auth, rate limits, idempotency, cancellation, and privacy tests pass.
5. **Real user study** - Input: approved protocol and recruited participants;
   output: anonymized records. Done after ethics/privacy review and analysis.
