---
# harcompanon-0stm
title: 'Repo hygiene: LICENSE, README, .env.example, gitignore'
status: completed
type: task
priority: normal
created_at: 2026-08-21T08:51:42Z
updated_at: 2026-08-21T09:15:09Z
parent: harcompanon-67aj
---

- [x] LICENSE = MIT (confirm with user before committing)
- [x] README with purpose (companion, not check-automation) + quickstart
- [x] .env.example documenting ANTHROPIC/OPENAI/GEMINI keys (no real secrets)
- [x] verify .gitignore ignores secrets + runs/ but NOT examples/

## Summary of Changes

LICENSE = MIT (2026 Nermin Caluk), applied per user's 'as suggested' go-ahead. README rewritten: purpose (companion, not check-automation), pipeline diagram, minimal/structured prompts, the two-senses-of-testing note, quickstart. .env.example lists ANTHROPIC/OPENAI/GEMINI keys with no secrets. .gitignore already ignored .env; appended a project section ignoring /runs/ and local secrets files while keeping /examples/ tracked.
