# Security and privacy

- Do not commit user PDFs, indexes, API keys, raw node notes, or participant data.
- PDF text is untrusted evidence and cannot alter system/tool policy.
- Validate type, size, page count, hashes, chunk IDs, and cited pages.
- Keep API keys server-side; redact authorization headers and environment values.
- Public demos require per-IP rate limits, upload/request/token/cost caps, 30s
  timeouts, bounded retries, isolated non-shell workers, and temporary-file TTL.
- Warn users not to upload personal, confidential, or copyrighted documents.
- Node notes remain in browser localStorage and are excluded from research calls
  unless the user explicitly selects and reviews them.
- Participant records use random IDs; consent/contact data is stored separately.
