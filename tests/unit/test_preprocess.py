"""Conventional software tests (pytest) for HAR preprocessing.

These are *checks* on our code — unrelated to "testing" in the RST sense.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from harcompanon.cli import app
from harcompanon.preprocess import NoiseRules, preprocess_file, preprocess_har

SAMPLE = Path(__file__).parents[1] / "data" / "sample.har"
runner = CliRunner()


def test_keeps_every_call_envelope() -> None:
    artifact = preprocess_file(SAMPLE)
    # Every entry survives as an envelope now (not just JSON calls).
    assert artifact.total_entries == 6
    assert len(artifact.calls) == 6
    # Two carry JSON bodies (the users GET and the login POST).
    assert artifact.json_body_count == 2
    urls = [c.url for c in artifact.calls]
    assert urls == [
        "https://api.example.com/v1/users",
        "https://cdn.example.com/logo.png",
        "https://cdn.example.com/font.woff2",
        "https://app.example.com/static/main.abc123.js",
        "https://api.example.com/v1/login",
        "https://api.example.com/health",
    ]


def test_json_bodies_kept_faithfully_non_json_stripped() -> None:
    calls = {c.url: c for c in preprocess_file(SAMPLE).calls}
    users = calls["https://api.example.com/v1/users"]
    assert isinstance(users.response_body, dict)
    assert users.response_body["total"] == 1
    # Non-JSON bodies become an explicit "<stripped: ...>" marker (never a bare null),
    # while the envelope (status / content-type) remains.
    image = calls["https://cdn.example.com/logo.png"]
    assert isinstance(image.response_body, str)
    assert image.response_body.startswith("<stripped: image/png")
    assert image.status == 200
    assert image.response_content_type == "image/png"
    health = calls["https://api.example.com/health"]
    assert isinstance(health.response_body, str)
    assert health.response_body.startswith("<stripped: text/plain")
    # The marker carries a human-readable size for non-base64 bodies.
    js = calls["https://app.example.com/static/main.abc123.js"]
    assert js.response_body == "<stripped: application/javascript, 16 B>"


def test_oversized_json_body_is_stripped_but_small_one_kept() -> None:
    big = json.dumps({"blob": "x" * 30000})
    small = json.dumps({"ok": True})

    def entry(path: str, text: str) -> dict[str, object]:
        return {
            "request": {"method": "GET", "url": f"https://api.example.com/{path}", "headers": []},
            "response": {
                "status": 200,
                "headers": [],
                "content": {"mimeType": "application/json", "text": text},
            },
        }

    raw = {"log": {"entries": [entry("big", big), entry("small", small)]}}
    calls = {c.url: c for c in preprocess_har(raw, NoiseRules(max_body_chars=20000)).calls}
    big_call = calls["https://api.example.com/big"]
    assert isinstance(big_call.response_body, str)
    assert "oversized" in big_call.response_body  # a giant JSON blob is stripped to a marker
    assert calls["https://api.example.com/small"].response_body == {"ok": True}  # small kept


def test_curated_headers_kept_and_content_type_excluded() -> None:
    users = {c.url: c for c in preprocess_file(SAMPLE).calls}["https://api.example.com/v1/users"]
    assert users.response_headers["content-security-policy"] == "default-src 'self'"
    assert users.response_headers["cache-control"] == "no-cache, private"
    # content-type has its own field; it is not duplicated into the headers dict.
    assert "content-type" not in users.response_headers


def test_sensitive_header_values_are_redacted() -> None:
    login = {c.url: c for c in preprocess_file(SAMPLE).calls}["https://api.example.com/v1/login"]
    # Presence kept, value gone — no token/cookie leaks into the cleaned artifact.
    assert login.request_headers["authorization"] == "<redacted>"
    assert login.response_headers["set-cookie"] == "<redacted>"
    dumped = login.model_dump_json()
    assert "super-secret-token" not in dumped
    assert "deadbeef" not in dumped
    # A non-sensitive header on the same response keeps its value.
    assert login.response_headers["content-security-policy"] == "default-src 'self'"
    # The request body is evidence and stays faithful.
    assert isinstance(login.request_body, dict)
    assert login.request_body["email"] == "ada@example.com"


def test_output_is_byte_stable_and_idempotent() -> None:
    first = preprocess_file(SAMPLE).to_canonical_json()
    second = preprocess_file(SAMPLE).to_canonical_json()
    assert first == second
    assert first.endswith("\n")


def test_noise_rules_json_detection() -> None:
    rules = NoiseRules()
    assert rules.is_json_content_type("application/json")
    assert rules.is_json_content_type("application/problem+json")
    assert rules.is_json_content_type("application/json; charset=utf-8")
    assert not rules.is_json_content_type("image/png")
    assert not rules.is_json_content_type(None)


def test_url_exclusion_rule_drops_matching_entries() -> None:
    artifact = preprocess_file(SAMPLE, NoiseRules(exclude_url_substrings=("cdn.example.com",)))
    urls = [c.url for c in artifact.calls]
    assert all("cdn.example.com" not in u for u in urls)
    assert "https://api.example.com/v1/users" in urls


def test_cli_preprocess_emits_json(tmp_path: Path) -> None:
    out = tmp_path / "cleaned.json"
    result = runner.invoke(
        app, ["preprocess", str(SAMPLE), "--output", str(out), "--no-security-scan"]
    )
    assert result.exit_code == 0
    text = out.read_text(encoding="utf-8")
    assert '"json_body_count": 2' in text
    assert "abc.def.ghi" in text
