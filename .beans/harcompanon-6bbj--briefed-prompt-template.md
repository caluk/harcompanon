---
# harcompanon-6bbj
title: Briefed prompt template
status: completed
type: task
priority: high
created_at: 2026-08-21T10:51:04Z
updated_at: 2026-08-23T08:29:06Z
parent: harcompanon-5kp7
---

Middle-tier prompt between minimal and structured. Assigns the instrument role + the session-based-testing / pre-go-live situation, but imposes NO output structure (no sections, no oracle/hypothesis/self-critique language) — clear water from structured.
- [x] prompts/briefed/v1.md with the {{artifact}} placeholder
- [x] role framing: instrument, not the tester, not the judge (human is)
- [x] situation: session-based testing before go-live
- [x] open-ended ask; no schema, no structural check (free-form like minimal)

## Summary of Changes
Added src/harcompanon/prompts/briefed/v1.md — the middle tier. Assigns the instrument role (not the tester, not the judge; human is) + the session-based-testing / pre-go-live situation, with an open-ended ask and NO output structure (clear water from structured). Free-form like minimal (no schema/structural check). Purpose: isolate the effect of role+situation (minimal->briefed) from the effect of imposing structure (briefed->structured).
