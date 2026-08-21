"""Core typed data models.

For now this holds the *cleaned artifact* that preprocessing produces — the faithful,
noise-stripped view of a HAR that later stages feed to the models. More core types (runs,
responses, findings, the RST ladder) will land alongside their own tasks.
"""

from __future__ import annotations

import json

from pydantic import BaseModel, JsonValue


class CleanedCall(BaseModel):
    """One API call kept from a HAR: bodies, status, and timing — nothing interpreted."""

    method: str
    url: str
    status: int
    started_at: str | None = None
    time_ms: float | None = None
    request_content_type: str | None = None
    request_body: JsonValue | None = None
    response_content_type: str | None = None
    response_body: JsonValue | None = None


class CleanedArtifact(BaseModel):
    """The result of preprocessing a HAR: the kept calls plus honest keep/drop counts."""

    source_har: str
    total_entries: int
    kept_entries: int
    dropped_entries: int
    calls: list[CleanedCall]

    def to_canonical_json(self) -> str:
        """Serialize deterministically and faithfully.

        Byte-stable across reruns (so a frozen fixture round-trips identically), while
        preserving each body's original key order — canonicalizing further would be
        interpretation, which preprocessing must never do.
        """
        payload = self.model_dump(mode="json")
        return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
