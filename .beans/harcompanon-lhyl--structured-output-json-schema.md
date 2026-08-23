---
# harcompanon-lhyl
title: Structured-output JSON schema
status: completed
type: task
priority: high
created_at: 2026-08-21T08:51:42Z
updated_at: 2026-08-23T08:29:06Z
parent: harcompanon-5kp7
blocked_by:
    - harcompanon-2wel
---

- [x] schemas/structured_response.schema.json matching the structured template (findings[] each with oracle label; self_critique; human_only_questions[]; hypotheses disclaimer)
- [x] (reframed) output is human-readable markdown, so this is a structural CONFORMANCE spec consumed by the checker, not a JSON-output schema / pydantic model

## Summary of Changes
Added src/harcompanon/schemas/structured_response.schema.json. Because structured emits human-readable markdown (per the approved wording), this is a structural conformance SPEC (required_sections + finding_fields) that the structural check (harcompanon-fvt4) will verify against the prose — not a JSON-Schema for forced JSON output, and not pydantic-generated. A coherence test asserts the spec's sections/fields actually appear in structured/v1.md. It is a presence check only; the human remains the sole judge.
