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


def redact_text(har_text: str, raw: dict[str, Any]) -> tuple[str, int]:
    """Replace each detected secret value in ``har_text``; return (text, occurrences_removed)."""
    removed = 0
    for secret in collect_secrets(raw):
        occurrences = har_text.count(secret)
        if occurrences:
            har_text = har_text.replace(secret, REDACTION)
            removed += occurrences
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
    remaining = sum(redacted_text.count(secret) for secret in collect_secrets(raw))
    return removed, remaining
