"""Typed data model for the cleaned HAR artifact that preprocessing produces.

The philosophy is "keep the whole request/response *envelope*, strip only the heavy/binary
*bodies*": every call's method, URL, status, timing, content types, and a curated set of
(mostly security-relevant) headers are kept, so the full API surface a tester scrutinises
survives; only noise bodies (images, fonts, JS, base64) are dropped, while JSON bodies are kept.
"""

from __future__ import annotations

import json

from pydantic import BaseModel, JsonValue


class CleanedCall(BaseModel):
    """One API call's envelope: metadata, curated headers, and JSON bodies only."""

    method: str
    url: str
    status: int
    started_at: str | None = None
    time_ms: float | None = None
    request_content_type: str | None = None
    response_content_type: str | None = None
    request_headers: dict[str, str] = {}
    response_headers: dict[str, str] = {}
    request_body: JsonValue | None = None
    response_body: JsonValue | None = None


class CleanedArtifact(BaseModel):
    """The result of preprocessing a HAR: every kept call's envelope plus honest counts."""

    source_har: str
    total_entries: int
    calls: list[CleanedCall]
    json_body_count: int

    def to_canonical_json(self) -> str:
        """Serialize deterministically and faithfully.

        Byte-stable across reruns (so a frozen fixture round-trips identically), while
        preserving each body's original key order — canonicalizing further would be
        interpretation, which preprocessing must never do.
        """
        payload = self.model_dump(mode="json")
        return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
