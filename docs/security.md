# Security and privacy

- Keep `.env`, API keys, private PDFs, local indexes, participant data, and raw
  private runs outside Git.
- Live evaluation requires both an environment key and explicit `--live`.
- Model requests use `store=false`, bounded output, retries, timeouts, steps,
  tokens, per-question cost, and total cost.
- Retrieved text is untrusted evidence. No role can execute shell, Python, or
  instructions embedded in a PDF.
- Trace stores input hashes and bounded structured outputs, never Authorization
  headers or complete prompts.
- Normal CI is offline and does not receive or call paid API secrets.
- Learning-map CI starts its API with `OPENAI_API_KEY` removed and verifies that
  health reports AI unavailable; model calls are replaced by test doubles.
- AI citations to unsupplied pages are removed. Nodes left without PDF evidence
  become excluded external-prerequisite suggestions; a goal without supplied
  evidence and all out-of-range pages remain hard errors.

This is a research prototype. It does not guarantee mathematical correctness or
the completeness of citations.

## Trust boundaries

- Browser: owns the selected local PDF, localStorage, map edits, and consent UI.
- Node BFF: accepts only the explicit grounded-question request and does not hold
  an OpenAI credential.
- Research API: serves only checked-in CC0 fixtures and deterministic tools.
- Learning-map API: holds the optional OpenAI key and accepts bounded JSON, never
  the PDF binary.
- OpenAI API: receives only the content explicitly described in the two consent
  stages. Model requests set `store=false` in the current implementation.

## Not a deployment security model

Both Python services intentionally bind to loopback for local development. They
have no authentication, tenant isolation, upload quarantine, durable encrypted
storage, or public rate limiting. Do not expose ports 8000 or 8765 to a network.
Authentication, abuse prevention, origin policy, data retention, and incident
response require a separate review before hosting.
