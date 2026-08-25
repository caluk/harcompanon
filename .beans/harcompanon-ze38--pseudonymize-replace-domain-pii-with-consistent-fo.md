---
# harcompanon-ze38
title: 'pseudonymize: replace domain PII with consistent, format-preserving synthetic data'
status: done
type: feature
priority: high
created_at: 2026-08-25T16:57:26Z
updated_at: 2026-08-25T17:40:00Z
parent: harcompanon-6dr7
---

redact masks SECRETS; domain PII (VINs, plates, IMEIs, deviceIds, addresses, mileage, user UUID in URL paths) is untouched and unsafe to send to 6 providers. Pseudonymize keeps evidence USABLE: consistent (same real->same synth) + format-preserving (UUID stays UUID-shaped, VIN 17-char, IMEI 15-digit) so structural findings survive; only identifiers change.
- [x] pseudonymize.py: key-based (configurable PII keys in JSON bodies) + pattern-based (UUID/VIN in URLs + bodies, whole-entry deep walk); shared consistent + idempotent mapping; format-preserving generators.
- [x] CLI 'harcompanon pseudonymize <har> [-o out]' + a change report (counts per category).
- [x] Tests: consistency, format-preservation, keyed + pattern replacement, numeric-lookalike guard, header/`:path` coverage.
- [x] Verify on Lexus: 41 values synthesized (uuid=10, vin=2, imei=1, key=15, number=13); real VINs/UUIDs gone everywhere, telematics readings preserved, still preprocesses 41/41 + scans clean.

Notes: VIN pattern requires a letter (avoids scrambling 17-digit telematics readings); IMEI is key-based only (a bare 15-digit run is more often a sensor value than a device id). Deep whole-entry pattern walk catches URLs in `request.url`, `_initiator.url`, `response.redirectURL`, and the HTTP/2 `:path` header; `_synth` is idempotent so re-passes never remap a generated value.
