---
# harcompanon-6auz
title: pyproject.toml + package skeleton
status: todo
type: task
priority: high
created_at: 2026-08-21T08:51:42Z
updated_at: 2026-08-21T08:51:42Z
parent: harcompanon-67aj
---

Installable package layout.
- [ ] pyproject.toml (build backend, project metadata, deps, entry point `harcompanon`)
- [ ] src/harcompanon/ package with __init__.py
- [ ] cli.py wiring subcommands: preprocess, run, check, judge, closeout (typer recommended; keep dep-light)
- [ ] `pip install -e .` works and `harcompanon --help` runs
