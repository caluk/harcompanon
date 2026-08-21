---
# harcompanon-svfv
title: Noise rules (configurable)
status: completed
type: task
priority: high
created_at: 2026-08-21T08:51:42Z
updated_at: 2026-08-21T09:33:15Z
parent: harcompanon-6dr7
---

Mechanical only.
- [x] default drop list: images, fonts, minified bundles, base64 blobs, non-JSON MIME types
- [x] URL-pattern + MIME-type filters, overridable via config
- [x] documented defaults; NO interpretation/highlighting

## Summary of Changes

Added src/harcompanon/preprocess/rules.py: NoiseRules (pydantic) with a blunt, mechanical keep-rule — keep a call only if request or response is JSON (json_markers default ('json',), so images/fonts/JS/HTML/plaintext/base64 all fall away for free) plus an optional exclude_url_substrings filter. Both are configurable and documented as revisable once real fixtures land. No interpretation or highlighting.
