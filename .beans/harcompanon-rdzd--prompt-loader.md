---
# harcompanon-rdzd
title: Prompt loader
status: completed
type: task
priority: normal
created_at: 2026-08-21T08:51:42Z
updated_at: 2026-08-23T08:29:06Z
parent: harcompanon-5kp7
---

- [x] prompts.py resolves (name, version) -> template text
- [x] names are 'minimal'/'structured' (never tier1/tier2)

## Summary of Changes
Added src/harcompanon/prompts.py: load_template(mode, version), available_modes() (discovered from folders — adding a mode is adding a folder), render_prompt() (substitutes {{artifact}}), and load_structured_spec(). Templates are package DATA loaded via importlib.resources (verified they ship in the wheel), so iterating on wording never touches pipeline code. Modes are minimal/briefed/structured (never tier1/2/3).
