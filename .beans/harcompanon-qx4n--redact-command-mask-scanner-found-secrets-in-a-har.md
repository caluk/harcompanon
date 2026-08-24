---
# harcompanon-qx4n
title: 'redact command: mask scanner-found secrets in a HAR'
status: completed
type: feature
priority: high
created_at: 2026-08-24T15:39:56Z
updated_at: 2026-08-24T15:48:42Z
parent: harcompanon-6dr7
---

Motivated by the predictwind forecast HARs: rich first-party evidence but real logged-in tokens (JWTs, Mapbox pk, Intercom auth), unsafe to commit or send.

- [x] collect_secrets(raw) in security.py: the raw (unmasked) secret VALUES the scanner detects (headers, query params, body patterns, credential fields, emails).
- [x] redact.py: replace every collected secret value with <REDACTED> in the raw HAR text; keep it valid JSON + preprocessable.
- [x] CLI 'harcompanon redact <har> -o <out>': write redacted copy, report count, and VERIFY no secret value remains (note: presence of sensitive header/field NAMES is still flagged by a re-scan — only the values are gone).
- [x] Tests: on secrets_sample.har, every planted secret value is gone; output still parses/preprocesses.

## Summary of Changes
Added collect_secrets(raw) to preprocess/security.py (raw values the scanner detects) + a REDACTED_MARKER the scanner now ignores. Added src/harcompanon/redact.py: redact_file replaces every detected secret VALUE with <REDACTED> in the raw HAR text (longest-first, literal), keeping valid JSON + preprocessable, and verifies 0 secret values remain. Wired 'harcompanon redact <har> [-o out]' (default <name>.redacted.har). Because the scanner now skips the placeholder, a redacted file SCANS CLEAN (round-trip). Verified on the real forecast.predictwind2.com.har: 3556 occurrences redacted, Mapbox pk token 1->0, JWTs 4->0, and the redacted copy scans 'no obvious secrets/PII'. 59 pytest green. This makes the rich predictwind forecast evidence safe to commit AND safe to send to models.
