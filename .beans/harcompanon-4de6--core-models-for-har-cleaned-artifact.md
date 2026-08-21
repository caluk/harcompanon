---
# harcompanon-4de6
title: Core models for HAR + cleaned artifact
status: completed
type: task
priority: high
created_at: 2026-08-21T08:51:42Z
updated_at: 2026-08-21T09:33:15Z
parent: harcompanon-6dr7
---

- [x] pydantic models: HarEntry, CleanedCall (request/response body, status, timing), CleanedArtifact
- [x] deterministic serialization (stable ordering) for reproducibility

## Summary of Changes

Added src/harcompanon/models.py with pydantic v2 models CleanedCall (method, url, status, started_at, time_ms, request/response content-type + body as pydantic.JsonValue) and CleanedArtifact (source + keep/drop counts + calls). Deliberately did NOT model a full HarEntry — the raw HAR is parsed as a dict and only the cleaned output is typed (modelling the whole HAR schema would be over-modelling). CleanedArtifact.to_canonical_json() is byte-stable and faithful: fixed top-level field order, indent=2, ensure_ascii=False, trailing newline, and it preserves each body's original key order (canonicalising further would be interpretation). Added pydantic to deps + the pydantic.mypy plugin.
