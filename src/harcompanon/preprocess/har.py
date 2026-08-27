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


def _human_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.0f} KB"
    return f"{num_bytes / (1024 * 1024):.1f} MB"


def _status_forbids_body(method: str, status: int) -> bool:
    """HTTP methods/statuses that carry no message body.

    A body attached to one of these is a *capture* artifact — most often a browser stapling
    cached content onto a ``304 Not Modified`` — not something the server sent. Surfacing it as
    a ``<stripped: ...>`` marker makes every model cry "protocol violation" about our pipeline
    instead of testing the API, so we drop it. HEAD, 204, 304 and all 1xx have no body.
    """
    return method.upper() == "HEAD" or status in (204, 304) or 100 <= status < 200


def _body(
    text: Any,
    is_json: bool,
    content_type: str | None,
    size: Any,
    encoding: Any,
    max_body_chars: int,
) -> JsonValue | None:
    """Parse JSON bodies faithfully; represent every other *present* body — and any oversized
    one — as an explicit ``<stripped: type, size>`` marker.

    A bare ``null`` for a non-JSON body reads to a model as "missing / mock data" — the
    marker says "a body was here and we deliberately dropped it", which is the truth. Bodies
    over ``max_body_chars`` are stripped too (marked ``oversized``) so a few giant blobs can't
    blow past the model's context window.
    """
    if not isinstance(text, str) or text == "":
        return None
    is_base64 = isinstance(encoding, str) and encoding.lower() == "base64"
    oversized = len(text) > max_body_chars
    if is_json and not is_base64 and not oversized:
        try:
            return cast(JsonValue, json.loads(text))
        except json.JSONDecodeError:
            pass  # present but unparseable — mark it stripped rather than dropping silently
    if isinstance(size, int) and size > 0:
        num_bytes: int | None = size
    elif is_base64:
        num_bytes = None  # a base64 string's length isn't the real byte size
    else:
        num_bytes = len(text.encode("utf-8"))
    suffix = f", {_human_size(num_bytes)}" if num_bytes else ""
    tag = " (oversized)" if oversized else ""
    return f"<stripped: {content_type or 'body'}{suffix}{tag}>"


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

    method = str(request.get("method", ""))
    status = int(response.get("status", 0) or 0)
    started = entry.get("startedDateTime")
    time_value = entry.get("time")
    return CleanedCall(
        method=method,
        url=url,
        status=status,
        started_at=started if isinstance(started, str) else None,
        time_ms=float(time_value) if isinstance(time_value, (int, float)) else None,
        request_content_type=request_ct,
        response_content_type=response_ct,
        request_headers=rules.select_headers(request.get("headers")),
        response_headers=rules.select_headers(response.get("headers")),
        request_body=_body(
            post.get("text"),
            rules.is_json_content_type(request_ct),
            request_ct,
            post.get("size"),
            None,
            rules.max_body_chars,
        ),
        response_body=(
            None
            if _status_forbids_body(method, status)
            else _body(
                content.get("text"),
                rules.is_json_content_type(response_ct),
                response_ct,
                content.get("size"),
                content.get("encoding"),
                rules.max_body_chars,
            )
        ),
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

    json_bodies = sum(
        1
        for c in calls
        if isinstance(c.response_body, dict | list) or isinstance(c.request_body, dict | list)
    )
    return CleanedArtifact(
        source_har=source_har,
        total_entries=total,
        calls=calls,
        json_body_count=json_bodies,
    )
