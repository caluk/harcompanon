---
# harcompanon-hgjv
title: HAR parser
status: completed
type: task
priority: high
created_at: 2026-08-21T08:51:42Z
updated_at: 2026-08-21T09:33:15Z
parent: harcompanon-6dr7
---

- [x] parse .har JSON, iterate entries
- [x] keep JSON API calls: request+response bodies, status codes, timings
- [x] unit tests over a tiny sample HAR

## Summary of Changes

Added src/harcompanon/preprocess/har.py: load_har() (validates a top-level JSON object), preprocess_har() (iterates log.entries defensively, extracts method/url/status/timing + request & response bodies, keeps only JSON API calls per NoiseRules), and preprocess_file() in preprocess/__init__.py. JSON bodies are parsed; base64 blobs are stripped; malformed JSON falls back to raw text. Covered by tests/unit/test_preprocess.py against tests/data/sample.har (a conventional test fixture, NOT the frozen RST fixture).
