---
# harcompanon-drq0
title: 'OpenAI-compatible providers: DeepSeek, Mistral, Kimi (Moonshot)'
status: completed
type: feature
priority: normal
created_at: 2026-08-25T07:55:44Z
updated_at: 2026-08-25T08:03:10Z
parent: harcompanon-smx3
---

Broaden the comparison beyond Claude/OpenAI/Gemini. These are OpenAI chat-completions compatible, so one generic provider covers all three.
- [x] OpenAICompatProvider(name, base_url, api_key_env, model): stateless chat.completions via the openai SDK with base_url override.
- [x] Register deepseek / mistral / kimi with base URLs + key envs + default models (verify per account).
- [x] .env.example: DEEPSEEK_API_KEY, MISTRAL_API_KEY, MOONSHOT_API_KEY.
- [x] Tests: registry builds all, protocol satisfied, base_url/key wired.

## Summary of Changes
Added src/harcompanon/providers/openai_compat.py: OpenAICompatProvider(name, base_url, api_key_env, model) — stateless chat.completions via the openai SDK with a base_url override, defensive text/usage extraction, no temperature. Registered deepseek (api.deepseek.com / DEEPSEEK_API_KEY / deepseek-chat), mistral (api.mistral.ai/v1 / MISTRAL_API_KEY / mistral-large-latest), kimi (api.moonshot.ai/v1 / MOONSHOT_API_KEY / kimi-k2-0905-preview) via small factory functions in config.py. Six providers now available. Defaults are best-guess — verify/override per account with --model (esp. the Kimi id). Added the 3 keys to .env.example. 60 pytest green.
