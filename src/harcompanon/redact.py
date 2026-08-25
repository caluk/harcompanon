"""Redact scanner-detected secrets from a HAR — a safe-to-commit *and* safe-to-send copy.

Replaces every secret VALUE the scanner finds (auth headers, tokens in query strings, body
keys/tokens, emails) with ``<REDACTED>`` in the raw HAR text. The result is still valid JSON
and still preprocesses. Note: the sensitive header/field *names* remain — so a re-scan still
notes their presence — but the values are gone. Bodies that were kept as evidence lose only
the matched secrets, nothing else.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from harcompanon.preprocess.security import REDACTED_MARKER, collect_secrets

REDACTION = REDACTED_MARKER


def _forms(secret: str) -> set[str]:
    """The shapes a secret can take in the raw HAR text.

    ``collect_secrets`` returns *parsed* values, but a value with quotes/backslashes/control
    chars (e.g. a cookie) appears **JSON-escaped** in the file — a literal replace of the parsed
    form would silently miss it. Cover the verbatim form and both JSON-escaped variants.
    """
    return {
        secret,
        json.dumps(secret, ensure_ascii=False)[1:-1],
        json.dumps(secret, ensure_ascii=True)[1:-1],
    }


def _occurrences(text: str, raw: dict[str, Any]) -> int:
    return sum(text.count(form) for secret in collect_secrets(raw) for form in _forms(secret))


def redact_text(har_text: str, raw: dict[str, Any]) -> tuple[str, int]:
    """Replace each detected secret value (in every form) in ``har_text``."""
    removed = 0
    for secret in collect_secrets(raw):
        for form in _forms(secret):
            count = har_text.count(form)
            if count:
                har_text = har_text.replace(form, REDACTION)
                removed += count
    return har_text, removed


def redact_file(path: Path, output: Path) -> tuple[int, int]:
    """Write a redacted copy of ``path`` to ``output``.

    Returns (values_redacted, secret_occurrences_remaining) — the second is a verification and
    should be 0.
    """
    text = path.read_text(encoding="utf-8")
    raw = json.loads(text)
    if not isinstance(raw, dict):
        raise ValueError(f"{path} is not a valid HAR file (expected a top-level JSON object).")

    redacted_text, removed = redact_text(text, raw)
    output.write_text(redacted_text, encoding="utf-8")
    remaining = _occurrences(redacted_text, raw)
    return removed, remaining
