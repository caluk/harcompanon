---
# harcompanon-d8p4
title: OpenAI provider
status: completed
type: task
priority: high
created_at: 2026-08-21T08:51:43Z
updated_at: 2026-08-24T15:16:53Z
parent: harcompanon-g06s
blocked_by:
    - harcompanon-urzt
---

- [x] implement Provider for OpenAI; stateless call; usage+cost capture

## Summary of Changes
Added src/harcompanon/providers/openai.py: OpenAIProvider via the official openai SDK, stateless single-shot through the Responses API (client.responses.create, input=prompt, max_output_tokens). Captures output_text + usage (input/output tokens) + latency + status, defensively via getattr. No temperature (model default) for cross-provider comparability. SDK imported lazily so dry-run/tests/registry need neither the package nor a key. Default model gpt-5 (override with --model). Registered in config.py. NOTE: OpenAI models aren't in the PRICING table yet, so cost shows '—' until exact prices are added.
