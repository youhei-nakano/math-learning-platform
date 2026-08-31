# Security Policy

## Supported version

Security fixes are applied to the latest commit on the `main` branch. This research prototype does not currently publish versioned releases or a hosted production service.

## Reporting a vulnerability

Please use GitHub Private Vulnerability Reporting for this repository when it is available. Do not place API keys, private PDFs, personal data, exploit details, private URLs, request IDs, or authentication material in a public Issue or Discussion.

If private reporting is unavailable, open a public Issue containing only a minimal, non-sensitive description and ask the maintainer to establish a private channel. Do not invent or guess a maintainer email address.

Include, when safe:

- affected commit and component;
- impact and prerequisites;
- minimal reproduction using synthetic data;
- whether credentials or user-provided documents could be exposed;
- suggested mitigation, if known.

## If an API key is exposed

1. Revoke the key immediately in the provider dashboard.
2. Create a replacement with the minimum required scope and budget.
3. Do not rely on deleting the key from the latest commit; inspect and sanitize Git history and logs.
4. Review OpenAI usage and GitHub Actions logs for unauthorized calls.
5. Add a regression check without recording the key value.

## Security boundaries

- OpenAI API keys are read only by server-side Python processes. They must not enter browser bundles or committed files.
- Live evaluation requires both an environment key and the explicit `--live` flag, with cost, token, step, retry, and timeout limits.
- Normal CI uses `contents: read`, removes the learning-map key during smoke tests, and does not call paid APIs.
- User PDFs remain browser-local. Only explicitly consented metadata or selected page excerpts may be sent to the learning-map API.
- Node notes, localStorage contents, participant data, private runs, and local indexes are not model inputs by default.
- Retrieved text is untrusted evidence. It is never executed as shell, Python, or a tool instruction.
- Citations are checked against retrieved or explicitly supplied document/page/chunk identifiers.

## Known limitations

- The local APIs have no authentication or rate limiting and must bind only to loopback interfaces.
- There is no hosted deployment security model.
- Browser localStorage is not encrypted application storage.
- Mathematical correctness and citation completeness still require human review.
- OCR, VLM, and arbitrary user-document hosting have not been security-reviewed.

See [docs/security.md](docs/security.md) for the implementation-level threat boundaries.
