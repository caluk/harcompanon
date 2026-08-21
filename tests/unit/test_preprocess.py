"""Conventional software tests (pytest) for HAR preprocessing.

These are *checks* on our code — unrelated to "testing" in the RST sense.
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from harcompanon.cli import app
from harcompanon.preprocess import NoiseRules, preprocess_file

SAMPLE = Path(__file__).parents[1] / "data" / "sample.har"
runner = CliRunner()


def test_keeps_only_json_api_calls() -> None:
    artifact = preprocess_file(SAMPLE)
    # 6 entries in, only the two JSON API calls kept (users GET, login POST).
    assert artifact.total_entries == 6
    assert artifact.kept_entries == 2
    assert artifact.dropped_entries == 4
    urls = [call.url for call in artifact.calls]
    assert urls == [
        "https://api.example.com/v1/users",
        "https://api.example.com/v1/login",
    ]


def test_bodies_are_parsed_faithfully() -> None:
    artifact = preprocess_file(SAMPLE)
    users, login = artifact.calls
    assert isinstance(users.response_body, dict)
    assert users.response_body["total"] == 1
    assert login.request_body == {"email": "ada@example.com", "password": "redacted"}
    assert isinstance(login.response_body, dict)
    assert login.response_body["token"] == "abc.def.ghi"
    assert login.time_ms == 88.0


def test_image_font_js_and_plaintext_are_dropped() -> None:
    artifact = preprocess_file(SAMPLE)
    urls = "\n".join(call.url for call in artifact.calls)
    for noise in ("logo.png", "font.woff2", "main.abc123.js", "/health"):
        assert noise not in urls


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


def test_url_exclusion_rule_drops_matching_calls() -> None:
    # Excluding "login" should drop the POST and leave only the users call.
    artifact = preprocess_file(SAMPLE, NoiseRules(exclude_url_substrings=("login",)))
    urls = [call.url for call in artifact.calls]
    assert urls == ["https://api.example.com/v1/users"]


def test_cli_preprocess_emits_json(tmp_path: Path) -> None:
    out = tmp_path / "cleaned.json"
    result = runner.invoke(app, ["preprocess", str(SAMPLE), "--output", str(out)])
    assert result.exit_code == 0
    text = out.read_text(encoding="utf-8")
    assert '"kept_entries": 2' in text
    assert "abc.def.ghi" in text
