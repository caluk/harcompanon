"""Noise rules for preprocessing — mechanical keep/drop decisions, no interpretation.

The rule is deliberately blunt: a HAR entry is kept only if it carries a JSON payload
(request or response). Images, fonts, minified bundles, HTML, plain text, and base64 blobs
all fall away for free because none of them are JSON. Everything here is configurable and
expected to be revised once real fixtures are in hand.
"""

from __future__ import annotations

from pydantic import BaseModel


class NoiseRules(BaseModel):
    """Configurable, mechanical rules for what counts as signal vs. noise."""

    #: Substrings that mark a content type as JSON (covers e.g. application/problem+json).
    json_markers: tuple[str, ...] = ("json",)
    #: Drop any call whose URL contains one of these substrings (case-insensitive).
    exclude_url_substrings: tuple[str, ...] = ()

    def is_json_content_type(self, content_type: str | None) -> bool:
        if not content_type:
            return False
        lowered = content_type.lower()
        return any(marker in lowered for marker in self.json_markers)

    def keeps(self, url: str, request_ct: str | None, response_ct: str | None) -> bool:
        """True iff this call is a JSON API call and not explicitly excluded by URL."""
        lowered_url = url.lower()
        if any(fragment in lowered_url for fragment in self.exclude_url_substrings):
            return False
        return self.is_json_content_type(request_ct) or self.is_json_content_type(response_ct)
