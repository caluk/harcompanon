---
# harcompanon-y34q
title: 'Storage: per-response JSON + comparison index'
status: completed
type: task
priority: high
created_at: 2026-08-21T08:51:43Z
updated_at: 2026-08-24T10:38:27Z
parent: harcompanon-g06s
blocked_by:
    - harcompanon-zdym
---

- [x] storage.py writes runs/<run-id>/responses/*.json with metadata
- [x] generate index.md as a SIDE-BY-SIDE comparison surface (the artifact the human reads when judging)

## Summary of Changes
Added src/harcompanon/storage.py: store_run writes runs/<run-id>/responses/<provider>__<mode>.json plus a generated index.md — an overview table (mode x provider: tokens/cost/latency) followed by each full response grouped by mode. The index states 'the human is the sole judge; this is a comparison surface, not a scoring.' Wired the whole slice into 'harcompanon run <fixture> [--provider] [--model] [--modes] [--dry-run] [--out]'. Verified end-to-end dry-run on dash.har (3 prompts -> 3 responses + index.md); 39 pytest green.
