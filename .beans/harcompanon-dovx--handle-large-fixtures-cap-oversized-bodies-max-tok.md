---
# harcompanon-dovx
title: 'Handle large fixtures: cap oversized bodies + max-tokens headroom + streaming'
status: completed
type: feature
priority: high
created_at: 2026-08-25T08:20:46Z
updated_at: 2026-08-25T08:24:57Z
parent: harcompanon-smx3
---

komoot (1.01M tokens) overflowed the 1M context; predictwind #2 was 637K tokens of mostly-giant-JSON noise. Also give output headroom.
- [x] NoiseRules.max_body_chars: strip any single body over the cap to a '<stripped: type, size (oversized)>' marker (JSON or not); envelope/headers stay.
- [x] Raise provider default max_tokens 8192 -> 16000.
- [x] Anthropic provider: stream (messages.stream + get_final_message) so large outputs can't time out or be cut.
- [x] CLI 'run --max-tokens' option, threaded to build_provider.
- [x] Tests: oversized body stripped; small body still parsed; max-tokens plumbing.

## Summary of Changes
NoiseRules.max_body_chars (default 20000): any single request/response body over the cap is stripped to a '<stripped: type, size (oversized)>' marker (JSON or not); envelope + headers stay. Effect on real fixtures: predictwind #2 637K->~60K tokens (~10x, ~$3.23->~$0.30); komoot 1.01M (was OVER the 1M context limit and ERRORED) -> ~60K tokens, now runnable. Raised provider default max_tokens 8192->16000; Anthropic provider now STREAMS (messages.stream + get_final_message) so large outputs can't hit the non-streaming timeout guard or be cut. Added 'run --max-tokens'. Note from the scan: outputs were never actually cut (all stop=end_turn, ~1.4-2.2K out); the real issue was INPUT bloat, which the cap fixes. 66 pytest green.
