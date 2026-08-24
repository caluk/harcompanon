---
# harcompanon-epuz
title: 'Config: provider registry + credentials'
status: completed
type: task
priority: high
created_at: 2026-08-21T08:51:43Z
updated_at: 2026-08-24T10:38:27Z
parent: harcompanon-g06s
---

- [x] config.py: provider list is config-driven
- [x] credentials from env / git-ignored secrets file, never hardcoded/committed
- [x] registry maps provider name -> class

## Summary of Changes
Added src/harcompanon/config.py: a name->factory registry (build_provider/available_providers) with per-provider DEFAULT_MODELS, and load_credentials() which loads a git-ignored .env via python-dotenv so provider SDKs read keys from the environment. Unknown provider names raise with the available list.
