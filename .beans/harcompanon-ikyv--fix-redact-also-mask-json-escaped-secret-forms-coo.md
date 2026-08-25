---
# harcompanon-ikyv
title: 'Fix redact: also mask JSON-escaped secret forms (cookies survived)'
status: completed
type: bug
priority: high
created_at: 2026-08-25T09:25:46Z
updated_at: 2026-08-25T09:27:21Z
parent: harcompanon-6dr7
---

collect_secrets returns PARSED values; redact did a literal text.replace, which misses values that appear JSON-escaped in the raw HAR (e.g., cookies with quotes). Result: those secrets survived AND the verification falsely reported 'clean'. Found on a real predictwind capture (3 cookie 'high' findings after a supposedly-clean redact).
- [x] redact each secret in all its forms: verbatim + json.dumps(ensure_ascii=False) + json.dumps(ensure_ascii=True), minus surrounding quotes.
- [x] verification counts the escaped forms too.
- [x] Test with a value containing a quote (JSON-escaped in the file).

## Summary of Changes
Root cause: collect_secrets returns PARSED values, but redact did a literal text.replace; a value with quotes/backslashes/control chars (e.g. a 2732-char cookie) appears JSON-ESCAPED in the file, so the replace matched 0 — and the verification used the same parsed form, so it also saw 0 and falsely reported 'clean'. Found on a real predictwind capture that still had 3 cookie 'high' findings after a supposedly-clean redact. Fix: _forms(secret) yields the verbatim value plus both json.dumps escaped variants (ensure_ascii False/True); redact_text and the remaining-check both iterate all forms. Re-verified on the real capture: 1956 redacted (was 1928), and it now scans 'no obvious secrets/PII'. Added a test with a quote-containing cookie. 67 pytest green.
