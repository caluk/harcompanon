"""Conventional software tests (pytest) for HAR redaction."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from harcompanon.cli import app
from harcompanon.preprocess import preprocess_file
from harcompanon.preprocess.security import collect_secrets
from harcompanon.redact import redact_file

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


def test_redacted_har_still_parses_and_preprocesses(tmp_path: Path) -> None:
    out = tmp_path / "redacted.har"
    redact_file(SECRETS_HAR, out)
    # Still valid JSON and still preprocesses without error.
    artifact = preprocess_file(out)
    assert artifact.total_entries > 0


def test_redacted_har_scans_clean(tmp_path: Path) -> None:
    from harcompanon.preprocess import SecurityScanner

    out = tmp_path / "redacted.har"
    redact_file(SECRETS_HAR, out)
    raw = json.loads(out.read_text(encoding="utf-8"))
    report = SecurityScanner().scan(raw)
    # The <REDACTED> placeholder is recognised, so nothing is flagged.
    assert not report.has_findings()


def test_cli_redact(tmp_path: Path) -> None:
    out = tmp_path / "clean.har"
    result = runner.invoke(app, ["redact", str(SECRETS_HAR), "-o", str(out)])
    assert result.exit_code == 0, result.output
    assert out.exists()
    assert "Verified" in result.output
    assert "hunter2password" not in out.read_text(encoding="utf-8")
