---
# harcompanon-goe6
title: 'Dev tooling: ruff + mypy + pytest'
status: completed
type: task
priority: high
created_at: 2026-08-21T08:51:42Z
updated_at: 2026-08-21T09:15:09Z
parent: harcompanon-67aj
---

Clean-repo bar.
- [x] ruff (lint+format) config in pyproject
- [x] mypy strict config
- [x] pytest config; tests/ layout (unit/ + integration/)
- [x] doc note distinguishing RST-sense testing from conventional pytest tests

## Summary of Changes

Configured ruff (lint + format, line-length 100, py311, curated rule set) with .beans excluded so ruff's python-in-markdown formatting can never gate machine-generated beans in CI. mypy strict over src + tests. pytest with tests/{unit,integration}. RST-vs-conventional-testing distinction noted in package docstring, test docstrings, and README. Verified: ruff check, ruff format --check, mypy, pytest all pass in a clean venv.
