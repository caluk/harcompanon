"""Noise rules for preprocessing — mechanical decisions, no interpretation.

The philosophy: keep every call's *envelope* (method, URL, status, timing, curated headers)
so the whole API surface survives — including non-JSON endpoints a tester cares about — and
strip only the heavy/binary *bodies* (images, fonts, JS/CSS, base64), while keeping JSON
bodies. Everything here is configurable and expected to be revised as fixtures teach us more.
"""

from __future__ import annotations

from pydantic import BaseModel

#: Curated headers worth keeping — mostly security- and behaviour-relevant. Lower-cased.
#: (content-type is captured separately as request/response_content_type.)
DEFAULT_KEPT_HEADERS: frozenset[str] = frozenset(
    {
        "content-security-policy",
        "cache-control",
        "set-cookie",
        "strict-transport-security",
        "x-frame-options",
        "x-content-type-options",
        "x-xss-protection",
        "referrer-policy",
        "permissions-policy",
        "access-control-allow-origin",
        "location",
        "www-authenticate",
        "server",
    }
)

#: Headers whose VALUES are secrets: keep the name (presence) but redact the value so the
#: cleaned artifact never carries a session token or key.
DEFAULT_REDACT_HEADERS: frozenset[str] = frozenset(
    {
        "set-cookie",
        "cookie",
        "authorization",
        "proxy-authorization",
        "x-api-key",
        "x-auth-token",
        "x-amz-security-token",
        "api-key",
    }
)

REDACTED = "<redacted>"


class NoiseRules(BaseModel):
    """Configurable, mechanical rules for what to keep from a HAR entry."""

    #: Substrings that mark a content type as JSON (covers e.g. application/problem+json).
    json_markers: tuple[str, ...] = ("json",)
    #: Drop an entry entirely if its URL contains one of these substrings (case-insensitive).
    exclude_url_substrings: tuple[str, ...] = ()
    #: Header names (lower-case) to retain in the cleaned artifact.
    kept_headers: frozenset[str] = DEFAULT_KEPT_HEADERS
    #: Retained headers whose values must be redacted (kept as presence only).
    redact_header_values: frozenset[str] = DEFAULT_REDACT_HEADERS

    def is_json_content_type(self, content_type: str | None) -> bool:
        if not content_type:
            return False
        lowered = content_type.lower()
        return any(marker in lowered for marker in self.json_markers)

    def should_drop(self, url: str) -> bool:
        """True if this entry should be dropped entirely (optional URL exclusion)."""
        lowered = url.lower()
        return any(fragment in lowered for fragment in self.exclude_url_substrings)

    def select_headers(self, headers: list[dict[str, object]] | None) -> dict[str, str]:
        """Keep the curated headers, redacting sensitive values; first value per name wins."""
        selected: dict[str, str] = {}
        for header in headers or []:
            if not isinstance(header, dict):
                continue
            name = str(header.get("name", "")).lower().lstrip(":")
            # Keep curated headers, and keep sensitive ones as redacted *presence*.
            if name not in self.kept_headers and name not in self.redact_header_values:
                continue
            value = REDACTED if name in self.redact_header_values else str(header.get("value", ""))
            selected.setdefault(name, value)
        return selected
