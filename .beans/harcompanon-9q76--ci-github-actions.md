---
# harcompanon-9q76
title: 'CI: GitHub Actions'
status: completed
type: task
priority: normal
created_at: 2026-08-21T08:51:42Z
updated_at: 2026-08-21T09:15:09Z
parent: harcompanon-67aj
---

- [x] workflow running ruff + mypy + pytest on push/PR
- [x] pinned Python version(s)

## Summary of Changes

Added .github/workflows/ci.yml: on push to main + all PRs, matrix over Python 3.11/3.12/3.13, installs -e .[dev], runs ruff check, ruff format --check, mypy, and pytest. fail-fast disabled so all versions report.
