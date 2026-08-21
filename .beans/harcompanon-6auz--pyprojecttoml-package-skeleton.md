---
# harcompanon-6auz
title: pyproject.toml + package skeleton
status: completed
type: task
priority: high
created_at: 2026-08-21T08:51:42Z
updated_at: 2026-08-21T09:15:09Z
parent: harcompanon-67aj
---

Installable package layout.
- [x] pyproject.toml (build backend, project metadata, deps, entry point `harcompanon`)
- [x] src/harcompanon/ package with __init__.py
- [x] cli.py wiring subcommands: preprocess, run, check, judge, closeout (typer recommended; keep dep-light)
- [x] `pip install -e .` works and `harcompanon --help` runs

## Summary of Changes

Installable package via hatchling with dynamic version from src/harcompanon/__init__.py. Console entry point `harcompanon` -> harcompanon.cli:app. cli.py is a Typer app with honest stubs for preprocess/run/check/judge/closeout (each reports 'not implemented' + its tracking bean and exits 2) plus a working `version` command. Verified in a clean venv: `pip install -e .` succeeds and `harcompanon --help` / `harcompanon version` run.
