---
# harcompanon-9iyo
title: Simple evals (learning extension, post-v1)
status: draft
type: epic
priority: deferred
tags:
    - future
    - evals
created_at: 2026-08-21T09:26:43Z
updated_at: 2026-08-21T09:26:43Z
---

Post-v1, personal/learning goal: add SIMPLE evals to get hands-on evals experience. NOT part of v1 scope.

Hard constraint (do not violate): the human remains the SOLE judge of prompt-response quality. Any eval lives in the mechanical POST-PROCESSING layer, firewalled from the human-judgment path — it is checking, never judging. Keep that seam clean (see docs/rst-glossary.md).

Candidate directions when this is picked up:
- [ ] structural-conformance eval over structured responses (extends harcompanon-fvt4)
- [ ] experimental/learning scorers the human can inspect (clearly labelled non-authoritative)
- [ ] regression view: rerun the frozen fixture against new model releases (longitudinal), with the construct-drift caveat surfaced

Needs refinement before work starts (hence draft).
