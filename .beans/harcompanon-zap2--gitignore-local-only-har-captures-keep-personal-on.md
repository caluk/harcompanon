---
# harcompanon-zap2
title: Gitignore local-only HAR captures (keep personal ones out of the repo)
status: completed
type: task
priority: high
created_at: 2026-08-25T07:35:03Z
updated_at: 2026-08-25T07:36:19Z
parent: harcompanon-smx3
---

User keeps real/personal captures (predictwind, komoot, google flights) in fixtures/ for local dev but must never commit them.
- [x] .gitignore: ignore all fixtures/*.har by default; explicitly allow only the safe committed ones (dash.har, perf.har).
- [x] Verify personal HARs + .redacted.har outputs are ignored; dash/perf stay tracked.

## Summary of Changes
Added a .gitignore rule: /fixtures/*.har ignored by default, with !/fixtures/dash.har and !/fixtures/perf.har allowed. Verified: komoot/predictwind/googlefl captures and *.redacted.har outputs are ignored; dash.har/perf.har stay tracked; personal HARs no longer show as untracked in git status. To commit a new safe fixture, add a matching '!' line. Also housekeeping: marked the six fully-completed epics done (67aj, 5kp7, g06s, kmc3, 7kr6, 6dr7).
