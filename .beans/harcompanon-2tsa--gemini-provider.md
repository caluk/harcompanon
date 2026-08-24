---
# harcompanon-2tsa
title: Gemini provider
status: completed
type: task
priority: high
created_at: 2026-08-21T08:51:43Z
updated_at: 2026-08-24T15:16:53Z
parent: harcompanon-g06s
blocked_by:
    - harcompanon-urzt
---

- [x] implement Provider for Google Gemini; stateless call; usage+cost capture

## Summary of Changes
Added src/harcompanon/providers/gemini.py: GeminiProvider via google-genai, stateless client.models.generate_content(model, contents=prompt, config=GenerateContentConfig(max_output_tokens)). Reads GEMINI_API_KEY or GOOGLE_API_KEY. Captures text + usage_metadata (prompt/candidates token counts) + latency, defensively. No temperature. Lazy SDK import. Default model gemini-2.5-pro (override with --model). Registered in config.py. Same PRICING note as OpenAI (cost '—' until priced). Also: run-id model slug now only strips 'claude-' so gpt-5 / gemini-2.5-pro stay readable; a 3-provider run id looks like dash_opus-4-8+gpt-5+gemini-2.5-pro_2026-08-24_17-16-12.
