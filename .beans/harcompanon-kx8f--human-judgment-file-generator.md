---
# harcompanon-kx8f
title: Human judgment file generator
status: completed
type: task
priority: normal
created_at: 2026-08-21T08:51:43Z
updated_at: 2026-08-24T11:18:27Z
parent: harcompanon-kmc3
blocked_by:
    - harcompanon-y34q
    - harcompanon-lhyl
---

- [x] judgment.py emits low-friction YAML pre-populated per finding
- [x] fields per finding: oracle_named (y/n), defensible (y/n), ladder_position, holistic note
- [x] structured responses -> findings from schema; minimal responses -> presented WHOLE, human segments findings (no LLM splitting = no interpretation). CONFIRM default with user.

## Summary of Changes
Added src/harcompanon/judgment.py: generate_judgment(run) emits a low-friction YAML form. For structured responses it lists each finding, parsed MECHANICALLY from the response's ## Findings section (splitting on '### ' headings) — post-processing, not a verdict. minimal/briefed responses are shown WHOLE with a single 'segment findings yourself' row (no LLM splitting — the user-confirmed default). Per-finding fields: oracle_named (yes/no), defensible (yes/no), ladder (slop|plausible|provisional|validated), note; plus a holistic_note per response. Wired 'harcompanon judge <run-dir>' (reads run.json, writes judgment.yml). The human is the sole judge; the tool only scaffolds.
