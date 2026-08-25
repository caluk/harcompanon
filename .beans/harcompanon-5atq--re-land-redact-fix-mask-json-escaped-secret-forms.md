---
# harcompanon-5atq
title: 'Re-land redact fix: mask JSON-escaped secret forms (PR #20 was orphaned)'
status: completed
type: bug
priority: critical
created_at: 2026-08-25T09:38:30Z
updated_at: 2026-08-25T09:39:53Z
parent: harcompanon-6dr7
---

PR #20 never merged (its branch got deleted before merge), so redact.py in main still does a literal text.replace and MISSES JSON-escaped values (cookies with quotes survive + verification falsely reports clean). Re-applying the fix.
- [x] _forms(secret): verbatim + json.dumps(ensure_ascii False/True)[1:-1].
- [x] redact_text + remaining-check iterate all forms.
- [x] test with quote-containing cookie.
- [x] verify on real komoot capture.

## Summary of Changes
Re-landed the redact escaping fix (PR #20 was orphaned when its branch was deleted before merge, so main still had the buggy literal-replace redact). _forms(secret) yields verbatim + both json.dumps escaped variants; redact_text and the remaining-check iterate all forms. Verified on the fresh komoot capture: 219 secrets redacted, rescans 'no obvious secrets/PII'. That komoot capture (cache-disabled) is strong: 323 entries, 317x 200, 48 JSON bodies, ~112K tokens. 67 pytest green.
