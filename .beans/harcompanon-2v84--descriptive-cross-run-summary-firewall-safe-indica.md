---
# harcompanon-2v84
title: Descriptive cross-run summary (firewall-safe indicators, not a verdict)
status: completed
type: feature
priority: normal
created_at: 2026-08-25T08:03:58Z
updated_at: 2026-08-25T08:08:09Z
parent: harcompanon-smx3
---

A thin, dependency-free aggregator over data we already compute (structural check + run metadata). Descriptive indicators only — NO LLM-as-judge (human is the sole judge of quality). Helps narrow fixtures and compare models across runs.
- [x] summary.py: load one or many run dirs; per response row: findings, oracles-named, conforms (structured only), in/out tokens, cost, latency, error.
- [x] a per-fixture rollup (which fixtures yield the most/richest structured findings).
- [x] CLI 'harcompanon summary <path>... [-o out.md]'; header states these are indicators, not a verdict.
- [x] Tests.

## Summary of Changes
Added src/harcompanon/summary.py: a thin, dependency-free descriptive aggregator (NO framework, NO LLM-as-judge). load_runs() reads one or many run dirs (run.json); summarize() emits a markdown table per (fixture, mode, provider, model) with findings + oracles-named + conforms (structured only, from the structural check) + tokens/cost/latency, plus a per-fixture rollup (Σ findings / Σ oracles / conforming) for narrowing fixtures. Header states loudly these are DESCRIPTIVE indicators, not a verdict; quality is judged by the human alone. Wired 'harcompanon summary <path>... [-o]'. 63 pytest green.
