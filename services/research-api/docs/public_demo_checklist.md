# Public demo deployment checklist

- [ ] Server-side secrets only; rotate staging keys before launch
- [ ] PDF MIME/header validation, 20 MB and 200 page limits
- [ ] 5 requests/minute/IP and daily project cost cap
- [ ] 30 second request timeout, one retry, cancellation propagation
- [ ] Isolated worker without shell, home-directory, or arbitrary network access
- [ ] Temporary upload deletion within 1 hour and documented retention
- [ ] Personal/confidential PDF warning and explicit external-send consent
- [ ] OCR/VLM disabled by default and separately consented
- [ ] Generic user errors; detailed secret-redacted server logs
- [ ] Abuse, prompt-injection, malformed PDF, and load tests
- [ ] CC0 sample PDFs only
- [ ] Privacy notice, license, contact, rollback, and incident procedures

No deployment or paid service was created in this work.
