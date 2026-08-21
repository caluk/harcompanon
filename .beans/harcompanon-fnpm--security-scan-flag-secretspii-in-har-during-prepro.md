---
# harcompanon-fnpm
title: 'Security scan: flag secrets/PII in HAR during preprocessing'
status: completed
type: feature
priority: high
created_at: 2026-08-21T09:57:34Z
updated_at: 2026-08-21T10:07:47Z
parent: harcompanon-6dr7
---

Add a mechanical secrets/PII scanner that runs as part of `preprocess` and FLAGS risks in the RAW har (what gets committed), so a HAR is never published with sensitive data. Motivated by real finding: a homepage capture still carried vendor emails + embedded Google API keys in JS bundles.

Design constraints:
- [x] Scans the RAW HAR (headers, URLs/query, request+response bodies), not just the cleaned output.
- [x] SEPARATE report; MUST NOT alter/annotate the cleaned artifact sent to models (purity principle intact). This is a safety check, not evidence interpretation.
- [x] Detectors (configurable): sensitive headers (cookie/authorization/set-cookie/x-api-key/...), private keys, AWS/Google/Slack keys, JWT/bearer tokens, tokens in query params, credential fields (password/secret/token) with values, emails/PII.
- [x] Severity levels (high/medium/low); values MASKED in the report (never store the full secret).
- [x] Wire into `harcompanon preprocess`: print a summary to stderr + optional --security-report file; loud caveat that it is heuristic, not a guarantee.
- [x] Tests with a synthetic HAR of planted (obviously fake) secrets; assert detection, masking, severity, and that cleaned output is unchanged.
- [x] Docs note: mechanical safety check, distinct from the evidence firewall.

## Summary of Changes

Added src/harcompanon/preprocess/security.py: a mechanical, configurable SecurityScanner over the RAW HAR (headers, URL query, request+response bodies) producing a SEPARATE masked SecurityReport — it never touches the cleaned evidence. Detectors: sensitive headers, private-key blocks, AWS/Google/Slack keys, JWT/bearer, credential fields (password/secret/token) with values, tokens in query params, emails/PII. Severity high/medium/low; findings deduped with occurrence counts; every value masked. Wired into `harcompanon preprocess` (summary to stderr, colour by severity, optional --security-report, --no-security-scan) with a loud 'heuristic, not a guarantee' caveat. Tested with a synthetic planted-secrets HAR (detection, masking, severity, and that cleaned output is unchanged). Validated on a real 55MB ad-heavy capture: refined the AWS pattern with word boundaries and switched the summary to count DISTINCT findings after the raw counts over-reported base64 false positives (226 -> 0 high). Docs note added to security.py and fixtures/README.
