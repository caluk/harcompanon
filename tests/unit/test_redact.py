"""Conventional software tests (pytest) for HAR redaction."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from harcompanon.cli import app
from harcompanon.preprocess import SecurityScanner, preprocess_file
from harcompanon.preprocess.security import collect_secrets
from harcompanon.redact import redact_file, redact_text

SECRETS_HAR = Path(__file__).parents[1] / "data" / "secrets_sample.har"
runner = CliRunner()

# The planted (obviously-fake) secret values in secrets_sample.har.
PLANTED = [
    "abcdef0123456789ABCDEFxyz",  # Authorization bearer
    "deadbeefcafebabe1234",  # Set-Cookie session
    "SUPERSECRETTOKENVALUE123",  # access_token query param
    "jane.doe@example.com",  # email (PII)
    "hunter2password",  # password field value
    "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",  # JWT signature
    "AKIAIOSFODNN7EXAMPLE",  # AWS key
]


def test_collect_secrets_finds_planted_values() -> None:
    raw = json.loads(SECRETS_HAR.read_text(encoding="utf-8"))
    values = collect_secrets(raw)
    assert "hunter2password" in values
    assert "SUPERSECRETTOKENVALUE123" in values
    # Longest-first ordering (so literal replacement is safe).
    assert values == sorted(values, key=len, reverse=True)


def test_redact_removes_every_planted_secret(tmp_path: Path) -> None:
    out = tmp_path / "redacted.har"
    removed, remaining = redact_file(SECRETS_HAR, out)
    assert removed > 0
    assert remaining == 0  # verification: no detected secret value survives

    text = out.read_text(encoding="utf-8")
    assert "<REDACTED>" in text
    for secret in PLANTED:
        assert secret not in text

    artifact = preprocess_file(out)
    assert artifact.total_entries == 4
    assert not SecurityScanner().scan(json.loads(text)).has_findings()
    # Re-running redaction must neither count placeholders as secrets nor report a failure.
    again = tmp_path / "again.har"
    assert redact_file(out, again) == (0, 0)
    assert again.read_text(encoding="utf-8") == text


def test_redact_masks_json_escaped_secret_values() -> None:
    # A cookie value with a double-quote is stored JSON-escaped in the file — a literal
    # replace of the parsed value would miss it (the bug this guards against).
    cookie = 'id="a"b; token=SECRETVALUE123'
    raw = {
        "log": {
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": "https://x/",
                        "headers": [{"name": "Cookie", "value": cookie}],
                    },
                    "response": {"status": 200, "headers": [], "content": {}},
                }
            ]
        }
    }
    text = json.dumps(raw)
    assert cookie not in text  # it is stored escaped; a naive replace would find nothing
    redacted, removed = redact_text(text, json.loads(text))
    assert removed > 0
    assert "SECRETVALUE123" not in redacted
    assert (
        json.loads(redacted)["log"]["entries"][0]["request"]["headers"][0]["value"] == "<REDACTED>"
    )


def test_cli_redact(tmp_path: Path) -> None:
    out = tmp_path / "clean.har"
    result = runner.invoke(app, ["redact", str(SECRETS_HAR), "-o", str(out)])
    assert result.exit_code == 0, result.output
    assert out.exists()
    assert "Verified" in result.output
    assert "hunter2password" not in out.read_text(encoding="utf-8")


@pytest.mark.parametrize("footer", ["\n-----END PRIVATE KEY-----", ""])
def test_redaction_removes_private_key_material_not_just_header(footer: str) -> None:
    # Deliberately fake material, including an interrupted capture without an END marker.
    material = "obviously-fake-key-material"
    pem = f"-----BEGIN PRIVATE KEY-----\n{material}{footer}"
    raw = {"log": {"entries": [{"response": {"content": {"text": pem}}}]}}
    redacted, removed = redact_text(json.dumps(raw), raw)
    assert removed == 1
    assert material not in redacted
    assert json.loads(redacted)["log"]["entries"][0]["response"]["content"]["text"] == "<REDACTED>"


def test_invalid_redaction_does_not_overwrite_output(tmp_path: Path) -> None:
    raw = {
        "log": {
            "entries": [
                {
                    "request": {
                        "url": "https://example.com/?token=n",
                        "postData": {"text": "line1\nline2"},
                    }
                }
            ]
        }
    }
    src, output = tmp_path / "in.har", tmp_path / "out.har"
    src.write_text(json.dumps(raw), encoding="utf-8")
    output.write_text("previous output", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        redact_file(src, output)
    assert output.read_text(encoding="utf-8") == "previous output"
