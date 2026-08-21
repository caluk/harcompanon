"""Parse a HAR and reduce it to a CleanedArtifact.

This is mechanical noise removal only: extract each entry's request/response bodies, status,
and timing, keep the JSON API calls, and drop the rest. Nothing here interprets or highlights
the evidence.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from pydantic import JsonValue

from harcompanon.models import CleanedArtifact, CleanedCall
from harcompanon.preprocess.rules import NoiseRules


def load_har(path: Path) -> dict[str, Any]:
    """Load a .har file as a raw dict (the HAR format is JSON with a top-level ``log``)."""
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a valid HAR file (expected a top-level JSON object).")
    return cast(dict[str, Any], data)


def _mime(container: dict[str, Any]) -> str | None:
    value = container.get("mimeType")
    return value if isinstance(value, str) and value else None


def _body(text: Any, is_json: bool, encoding: Any = None) -> JsonValue | None:
    """Extract a body faithfully: parse JSON when it is JSON, drop base64 blobs as noise."""
    if not isinstance(text, str) or text == "":
        return None
    if isinstance(encoding, str) and encoding.lower() == "base64":
        return None
    if is_json:
        try:
            return cast(JsonValue, json.loads(text))
        except json.JSONDecodeError:
            return text
    return text


def _extract_call(entry: dict[str, Any], rules: NoiseRules) -> CleanedCall | None:
    request = entry.get("request")
    response = entry.get("response")
    if not isinstance(request, dict) or not isinstance(response, dict):
        return None

    url = str(request.get("url", ""))
    post_raw = request.get("postData")
    post: dict[str, Any] = post_raw if isinstance(post_raw, dict) else {}
    content_raw = response.get("content")
    content: dict[str, Any] = content_raw if isinstance(content_raw, dict) else {}
    request_ct = _mime(post)
    response_ct = _mime(content)

    if not rules.keeps(url, request_ct, response_ct):
        return None

    started = entry.get("startedDateTime")
    time_value = entry.get("time")
    return CleanedCall(
        method=str(request.get("method", "")),
        url=url,
        status=int(response.get("status", 0) or 0),
        started_at=started if isinstance(started, str) else None,
        time_ms=float(time_value) if isinstance(time_value, (int, float)) else None,
        request_content_type=request_ct,
        request_body=_body(post.get("text"), rules.is_json_content_type(request_ct)),
        response_content_type=response_ct,
        response_body=_body(
            content.get("text"),
            rules.is_json_content_type(response_ct),
            encoding=content.get("encoding"),
        ),
    )


def preprocess_har(
    raw: dict[str, Any],
    rules: NoiseRules | None = None,
    *,
    source_har: str = "",
) -> CleanedArtifact:
    """Reduce a raw HAR dict to a CleanedArtifact of JSON API calls."""
    rules = rules or NoiseRules()
    log = raw.get("log")
    entries = log.get("entries") if isinstance(log, dict) else None
    entries = entries if isinstance(entries, list) else []

    calls: list[CleanedCall] = []
    total = 0
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        total += 1
        call = _extract_call(entry, rules)
        if call is not None:
            calls.append(call)

    return CleanedArtifact(
        source_har=source_har,
        total_entries=total,
        kept_entries=len(calls),
        dropped_entries=total - len(calls),
        calls=calls,
    )
