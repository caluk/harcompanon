"""Redact scanner-detected secrets from a HAR; review the result before sharing.

Replaces every secret VALUE the scanner finds (auth headers, tokens in query strings, body
keys/tokens, emails) with ``<REDACTED>`` in the raw HAR text. The result is still valid JSON
and still preprocesses. Sensitive header/field names remain; the scanner ignores the
redaction marker. Literal replacement can also affect matching text elsewhere in the HAR.
Detection is heuristic and does not guarantee that all sensitive data is removed.
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
        for form in sorted(_forms(secret), key=len, reverse=True):
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
    # Literal substitution must not publish malformed JSON or overwrite an existing output
    # with it (e.g. a short secret may also match a JSON escape sequence).
    json.loads(redacted_text)
    output.write_text(redacted_text, encoding="utf-8")
    remaining = _occurrences(redacted_text, raw)
    return removed, remaining
