---
# harcompanon-dm8a
title: Freeze the real fixture
status: completed
type: task
priority: high
created_at: 2026-08-21T08:51:42Z
updated_at: 2026-08-24T15:27:14Z
parent: harcompanon-6dr7
blocked_by:
    - harcompanon-4dj8
---

Needs the user-provided HAR.
- [x] add real HAR under fixtures/ byte-identical
- [x] record provenance (what app/session, capture date) in docs
- [x] confirm it survives preprocessing into sensible cleaned output

## Summary of Changes
Froze the OrangeHRM public-demo captures as committed fixtures: fixtures/dash.har (primary, 25 entries, 7 dashboard JSON endpoints) and fixtures/perf.har (secondary, performance module; duplicate workweek/holidays calls). Both from opensource-demo.orangehrmlive.com, captured 2026-06-18, throwaway demo data. Security scan: 0 high / 0 medium each (1 low = OrangeHRM's own vendor support email in their public app.js — safe). Both preprocess cleanly (25/25 and 24/24 envelopes, 7 JSON bodies). Provenance + redaction guidance recorded in fixtures/README.md.
