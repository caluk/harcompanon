---
# harcompanon-q11q
title: Run naming + cost normalization + stripped-body markers
status: completed
type: task
priority: high
created_at: 2026-08-24T11:09:34Z
updated_at: 2026-08-24T11:12:26Z
parent: harcompanon-6dr7
---

Polish from the first live run:
- [x] Readable run id: fixture + model slug + CET timestamp (no trailing HHMMSS integer), OS-safe length.
- [x] created_at in CET (local, with offset) instead of UTC.
- [x] estimate_cost normalizes dated model ids (claude-haiku-4-5-20251001 -> claude-haiku-4-5) so cost isn't dropped.
- [x] Non-JSON bodies shown as an explicit '<stripped: type, size>' marker instead of null (+ drop the misleading response_bytes field, which made models read 304s as 'body present'). Models were misreading null bodies as 'mock/incomplete data'.

## Summary of Changes
Run ids are now readable: build_run_id() -> {fixture}_{model-slug}_{CET date_time} (e.g. dash_opus-4-8_2026-08-24_13-11-56); created_at stamped in Europe/Berlin (CET, with offset). estimate_cost() strips a trailing -YYYYMMDD so dated snapshot ids (claude-haiku-4-5-20251001) still price. Preprocessing: dropped the response_bytes field and now represents every present non-JSON body as an explicit '<stripped: <content-type>, <size>>' marker (JSON bodies still parsed faithfully); json_body_count counts only real dict/list bodies. Added tzdata dep so ZoneInfo resolves on any platform. 41 pytest green; verified markers + run id on dash.har.
