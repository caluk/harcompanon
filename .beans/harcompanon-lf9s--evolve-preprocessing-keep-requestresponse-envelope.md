---
# harcompanon-lf9s
title: 'Evolve preprocessing: keep request/response envelope + curated headers'
status: completed
type: feature
priority: high
created_at: 2026-08-23T08:42:04Z
updated_at: 2026-08-23T08:47:59Z
parent: harcompanon-6dr7
---

Real fixtures (OrangeHRM) showed the JSON-only rule discards the richest testable signal: non-JSON endpoints (image BOLA, POST /events/push) and security headers (CSP, cache-control, HSTS). Shift the philosophy.

- [x] Keep EVERY entry's envelope: method, url, status, timing, content-types.
- [x] Retain a curated set of (mostly security-relevant) headers: CSP, cache-control, HSTS, x-frame-options, x-content-type-options, set-cookie (presence), location, server, etc.
- [x] Redact sensitive header VALUES in the cleaned artifact (authorization, cookie, set-cookie, api keys) — presence without the secret.
- [x] Strip only heavy/binary BODIES (images, fonts, JS/CSS, base64); keep JSON bodies faithfully.
- [x] Add response body size so 'returned a 12KB image' is visible without the bytes.
- [x] Update CleanedCall/CleanedArtifact, NoiseRules, parser, CLI message, and tests.
- [x] Mechanical only — still no interpretation/highlighting.

## Summary of Changes
Shifted preprocessing from 'keep only JSON calls' to 'keep every call ENVELOPE, strip only heavy/binary bodies'. CleanedCall now carries request/response headers (curated) + response_bytes; CleanedArtifact reports total_entries, all calls, and json_body_count. NoiseRules gains kept_headers (CSP, cache-control, HSTS, x-frame-options, x-content-type-options, set-cookie, location, server, ...) and redact_header_values (authorization/cookie/set-cookie/api-keys kept as '<redacted>' presence, never the secret) plus optional exclude_url_substrings to drop entries. Parser keeps all valid entries, extracts curated headers, parses JSON bodies only, and records response size. CLI message updated. Verified on dash.har: the previously-dropped viewPhoto (BOLA), POST /events/push, and CSP/cache-control headers now appear in the cleaned output — enabling the richer findings the workshop flyover demonstrated. 27 pytest green; still purely mechanical (no interpretation).
