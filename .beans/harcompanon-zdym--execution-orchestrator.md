---
# harcompanon-zdym
title: Execution orchestrator
status: completed
type: task
priority: high
created_at: 2026-08-21T08:51:43Z
updated_at: 2026-08-24T10:38:27Z
parent: harcompanon-g06s
blocked_by:
    - harcompanon-urzt
    - harcompanon-epuz
    - harcompanon-rdzd
---

- [x] execution.py: run = one fixture x all configured providers x both prompts
- [x] stateless calls, no chat/memory/personalization
- [x] capture metadata: model, prompt version, timestamp, tokens, cost, latency

## Summary of Changes
Added src/harcompanon/execution.py: run_benchmark(fixture, providers, modes) preprocesses the fixture once, renders each mode's prompt, and runs every (provider, mode) as a stateless call, collecting RunResponse records (provider, model, mode, version, prompt_chars, dry_run, error, RawResponse) into a RunResult (run_id, fixture, created_at). A provider exception is captured per-cell (doesn't sink the run). Added a --dry-run path that renders prompts and exercises the whole pipeline with NO API call — so the layer is fully testable without keys.
