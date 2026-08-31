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

This is a research prototype. It does not guarantee mathematical correctness or
the completeness of citations.
