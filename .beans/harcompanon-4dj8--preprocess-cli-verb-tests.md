---
# harcompanon-4dj8
title: preprocess CLI verb + tests
status: completed
type: task
priority: normal
created_at: 2026-08-21T08:51:42Z
updated_at: 2026-08-21T09:33:15Z
parent: harcompanon-6dr7
---

- [x] `harcompanon preprocess <har>` emits cleaned artifact
- [x] round-trip/idempotence test; byte-stable output

## Summary of Changes

Wired the real `harcompanon preprocess <har> [-o out]` command (Typer, Annotated params) — writes canonical cleaned JSON to stdout or a file. Tests cover keep/drop counts, faithful body parsing, base64/image/font/js/plaintext dropping, the URL-exclusion rule, byte-stable + idempotent output, and the CLI end to end. Verified in a clean venv: ruff, ruff format, strict mypy, 10 pytest all pass; `harcompanon preprocess tests/data/sample.har` keeps 2/6 calls.
