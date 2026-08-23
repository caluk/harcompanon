"""Parse a HAR and reduce it to a CleanedArtifact.

Mechanical noise removal only. Every call's envelope is kept (method, URL, status, timing,
curated headers, content types); only heavy/binary bodies are dropped, while JSON bodies are
kept. Nothing here interprets or highlights the evidence.
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


def _json_body(text: Any, is_json: bool, encoding: Any = None) -> JsonValue | None:
    """Keep a body only if it is JSON; parse it. Everything else (incl. base64) is dropped."""
    if not is_json or not isinstance(text, str) or text == "":
        return None
    if isinstance(encoding, str) and encoding.lower() == "base64":
        return None
    try:
        return cast(JsonValue, json.loads(text))
    except json.JSONDecodeError:
        return None


def _response_bytes(content: dict[str, Any]) -> int | None:
    """Best-effort size of the response body, even when the body itself is stripped."""
    size = content.get("size")
    if isinstance(size, int) and size >= 0:
        return size
    text = content.get("text")
    encoding = content.get("encoding")
    if isinstance(text, str) and not (isinstance(encoding, str) and encoding.lower() == "base64"):
        return len(text.encode("utf-8"))
    return None


def _extract_call(entry: dict[str, Any], rules: NoiseRules) -> CleanedCall | None:
    request = entry.get("request")
    response = entry.get("response")
    if not isinstance(request, dict) or not isinstance(response, dict):
        return None

    url = str(request.get("url", ""))
    if rules.should_drop(url):
        return None

    post_obj = request.get("postData")
    post: dict[str, Any] = post_obj if isinstance(post_obj, dict) else {}
    content_obj = response.get("content")
    content: dict[str, Any] = content_obj if isinstance(content_obj, dict) else {}
    request_ct = _mime(post)
    response_ct = _mime(content)

    started = entry.get("startedDateTime")
    time_value = entry.get("time")
    return CleanedCall(
        method=str(request.get("method", "")),
        url=url,
        status=int(response.get("status", 0) or 0),
        started_at=started if isinstance(started, str) else None,
        time_ms=float(time_value) if isinstance(time_value, (int, float)) else None,
        request_content_type=request_ct,
        response_content_type=response_ct,
        request_headers=rules.select_headers(request.get("headers")),
        response_headers=rules.select_headers(response.get("headers")),
        request_body=_json_body(post.get("text"), rules.is_json_content_type(request_ct)),
        response_body=_json_body(
            content.get("text"),
            rules.is_json_content_type(response_ct),
            encoding=content.get("encoding"),
        ),
        response_bytes=_response_bytes(content),
    )


def preprocess_har(
    raw: dict[str, Any],
    rules: NoiseRules | None = None,
    *,
    source_har: str = "",
) -> CleanedArtifact:
    """Reduce a raw HAR dict to a CleanedArtifact of call envelopes (JSON bodies kept)."""
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

    json_bodies = sum(1 for c in calls if c.response_body is not None or c.request_body is not None)
    return CleanedArtifact(
        source_har=source_har,
        total_entries=total,
        calls=calls,
        json_body_count=json_bodies,
    )
