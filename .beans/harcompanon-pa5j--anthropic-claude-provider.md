---
# harcompanon-pa5j
title: Anthropic (Claude) provider
status: completed
type: task
priority: high
created_at: 2026-08-21T08:51:43Z
updated_at: 2026-08-24T10:38:27Z
parent: harcompanon-g06s
blocked_by:
    - harcompanon-urzt
---

- [x] implement Provider for Claude via official SDK; stateless call; usage+cost capture

## Summary of Changes
Added src/harcompanon/providers/anthropic.py: AnthropicProvider using the official anthropic SDK, stateless messages.create (model claude-opus-4-8 default). Per the Claude API reference, sends NO temperature/top_p/budget_tokens (rejected on Opus 4.8) and leaves sampling at default for comparability. Captures text, input/output tokens, cost (via pricing table), latency, and stop_reason. The SDK is imported lazily inside complete() so --dry-run and tests need no SDK/key.
