---
# harcompanon-hcpr
title: Update README for redact, summary, six providers, full CLI
status: completed
type: task
priority: normal
created_at: 2026-08-25T09:10:41Z
updated_at: 2026-08-25T09:10:41Z
parent: harcompanon-smx3
---

README had fallen behind (two prompt tiers, three providers, no redact/check/summary).
- [x] Reflect: three prompt tiers, six providers, security scan, redact, oversized-body stripping, full CLI (preprocess/redact/run/check/judge/closeout/summary), fixtures policy, methodology link.

## Summary of Changes
Rewrote README.md: the pipeline diagram now includes the security scan, redact, and the check→judge→closeout→summary post-run steps; documents all three prompt tiers (minimal/briefed/structured), all six providers, the oversized-body cap, the full CLI verb list with flags, the fixtures policy (only safe public-demo captures committed; personal ones redacted + local-only), and links docs/methodology.md. Docs-only.
