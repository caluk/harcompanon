---
# harcompanon-s053
title: Session close-out generator
status: completed
type: task
priority: normal
created_at: 2026-08-21T08:51:43Z
updated_at: 2026-08-24T11:18:27Z
parent: harcompanon-kmc3
blocked_by:
    - harcompanon-zdym
---

- [x] closeout.py emits a report scaffold from the five debrief questions (what did you do; how did it go; did you notice specific problems; how did you evaluate them; now what), pre-filled with run metadata

## Summary of Changes
Added src/harcompanon/closeout.py: generate_closeout(run) emits a markdown scaffold with the five RST session-debrief questions (what did you do / how did it go / did you notice problems / how did you evaluate them / now what), pre-filled with run metadata (fixture, providers, modes, created, total cost) and question 1 auto-drafted. Wired 'harcompanon closeout <run-dir>'. Also added run.json persistence + load_run() to storage so judge/closeout can reload a run.
