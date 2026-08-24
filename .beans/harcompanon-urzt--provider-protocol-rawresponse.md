---
# harcompanon-urzt
title: Provider protocol + RawResponse
status: completed
type: task
priority: high
created_at: 2026-08-21T08:51:43Z
updated_at: 2026-08-24T10:38:27Z
parent: harcompanon-g06s
---

- [x] providers/base.py: Provider protocol with complete(prompt)->RawResponse (single rendered user message keeps providers uniform)
- [x] RawResponse carries provider, model, text, input/output tokens, cost_usd, latency_ms, stop_reason (dropped raw payload as noise)
- [x] adding a provider = one file + one config entry (no pipeline changes)

## Summary of Changes
Added src/harcompanon/providers/base.py: runtime_checkable Provider protocol (name, model, complete(prompt)->RawResponse), the RawResponse pydantic model (text + usage + cost + latency + stop_reason), a PRICING table, and estimate_cost(). Deliberately single-prompt (the rendered template is one user message) for cross-provider comparability, and no raw payload in RawResponse (kept it clean). Adding a provider is one class + one registry entry.
