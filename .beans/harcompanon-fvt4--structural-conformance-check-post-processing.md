---
# harcompanon-fvt4
title: Structural conformance check (post-processing)
status: completed
type: task
priority: normal
created_at: 2026-08-21T08:51:43Z
updated_at: 2026-08-24T15:23:41Z
parent: harcompanon-7kr6
blocked_by:
    - harcompanon-lhyl
    - harcompanon-y34q
---

Mechanical post-processing; NEVER a quality verdict.
- [x] validate structured responses against structured schema
- [x] emit structural_check.md as present/absent CHECKLIST
- [x] correctly flags missing schema elements (criterion 7)
- [x] naming + docstrings state 'post-processing, not judging'

## Summary of Changes
Added src/harcompanon/structural_check.py: check_structured(text) mechanically verifies a structured response has the shape the prompt asked for — required sections present (## headings from schemas/structured_response.schema.json) and per-finding Observation/Oracle/Status fields — and returns a StructuralReport (present/absent, conforming-findings count, conforms()). check_run() runs it over structured responses only (other modes have no schema). report_markdown() emits a present/absent CHECKLIST that states loudly it is POST-PROCESSING, 'not a quality verdict; quality is judged by the human alone'. Pure string-presence (no AI, no interpretation). Wired 'harcompanon check <run-dir>' -> structural_check.md; removed the last _not_implemented stub (all verbs now real). Verified it correctly flags missing sections and missing finding fields (criterion 7). 54 pytest green.
