---
# harcompanon-nyfb
title: Structured prompt template
status: completed
type: task
priority: high
created_at: 2026-08-21T08:51:42Z
updated_at: 2026-08-23T08:29:06Z
parent: harcompanon-5kp7
blocked_by:
    - harcompanon-2wel
---

- [x] prompts/structured/v1.md requiring: a LABELED oracle per finding, a self-critique section, an explicit list of questions only a human can answer, and a disclaimer that interpretations are hypotheses not findings

## Summary of Changes
Added src/harcompanon/prompts/structured/v1.md (the approved S1 + session/pre-go-live note). Requires exactly: ## Findings (each with Observation, a LABELED Oracle, and Status), ## Questions only a human can answer, and ## Self-critique; plus 'interpretations are hypotheses, not findings' and the instrument/human-is-judge framing + a 'surface risk, do not reassure' steer (exclusive to this tier). Outputs human-readable markdown (not forced JSON) so the structural check actually measures compliance rather than trivially passing.
