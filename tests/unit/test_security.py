"""Conventional software tests (pytest) for the secrets/PII scanner.

Checks on our code — not "testing" in the RST sense. The fixture contains only
obviously-fake, well-known example secrets (AWS's example key, the standard example JWT).
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from harcompanon.cli import app
from harcompanon.preprocess import SecurityScanner, Severity, preprocess_har, scan_file

SECRETS = Path(__file__).parents[1] / "data" / "secrets_sample.har"
runner = CliRunner()

# Full secret values that must NEVER appear (unmasked) in any report.
RAW_SECRETS = [
    "SUPERSECRETTOKENVALUE123",
    "deadbeefcafebabe1234",
    "hunter2password",
    "AKIAIOSFODNN7EXAMPLE",
    "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
]


def test_scanner_finds_expected_categories() -> None:
    report = scan_file(SECRETS)
    categories = {f.category for f in report.findings}
    for expected in (
        "header:authorization",
        "header:set-cookie",
        "query:access_token",
        "field:password",
        "email",
        "jwt",
        "aws_access_key",
        "google_api_key",
    ):
        assert expected in categories, f"missing {expected}: {categories}"


def test_detects_suffixed_and_escaped_credential_fields() -> None:
    from harcompanon.preprocess.security import collect_secrets

    # A body serialized as a JSON *string* inside another body: quotes are backslash-escaped,
    # and the key carries a prefix (publicApiToken / refreshToken) — both defeated the old regex.
    inner = json.dumps({"publicApiToken": "bd4c129e633944a4e2f794ae236720bb", "siteType": "web"})
    raw = {
        "log": {
            "entries": [
                {
                    "request": {"method": "GET", "url": "https://x/", "headers": []},
                    "response": {
                        "status": 200,
                        "headers": [],
                        "content": {
                            "mimeType": "application/json",
                            "text": json.dumps({"cfg": inner}),
                        },
                    },
                }
            ]
        }
    }
    secrets = collect_secrets(raw)
    assert "bd4c129e633944a4e2f794ae236720bb" in secrets  # token caught despite escaping + prefix
    assert "web" not in secrets  # short non-secret value not collected


def test_severity_classification() -> None:
    report = scan_file(SECRETS)
    by_cat = {f.category: f.severity for f in report.findings}
    assert report.has_high()
    assert by_cat["header:authorization"] is Severity.HIGH
    assert by_cat["field:password"] is Severity.HIGH
    assert by_cat["aws_access_key"] is Severity.HIGH
    assert by_cat["google_api_key"] is Severity.MEDIUM
    assert by_cat["jwt"] is Severity.MEDIUM
    assert by_cat["email"] is Severity.LOW


def test_report_masks_every_secret() -> None:
    report = scan_file(SECRETS)
    markdown = report.to_markdown()
    for secret in RAW_SECRETS:
        assert secret not in markdown, f"unmasked secret leaked: {secret}"


def test_scan_does_not_touch_cleaned_evidence() -> None:
    raw = json.loads(SECRETS.read_text(encoding="utf-8"))
    raw_before = json.dumps(raw)
    before = preprocess_har(raw, source_har="secrets_sample.har").to_canonical_json()
    SecurityScanner().scan(raw, source_har="secrets_sample.har")
    after = preprocess_har(raw, source_har="secrets_sample.har").to_canonical_json()
    # The scan must not mutate the raw HAR or change the cleaned artifact.
    assert before == after
    assert json.dumps(raw) == raw_before
    assert "hunter2password" in before  # the cleaned evidence is faithful, not redacted


def test_clean_har_reports_no_findings() -> None:
    # A genuinely clean HAR — no headers, no PII, plain JSON body.
    raw = {
        "log": {
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": "https://api.example.com/status",
                        "headers": [],
                    },
                    "response": {
                        "status": 200,
                        "headers": [],
                        "content": {"mimeType": "application/json", "text": '{"ok": true}'},
                    },
                }
            ]
        }
    }
    report = SecurityScanner().scan(raw, source_har="clean")
    assert not report.has_findings()
    assert "no obvious secrets" in report.summary_line()


def test_cli_warns_and_writes_report(tmp_path: Path) -> None:
    out = tmp_path / "cleaned.json"
    rep = tmp_path / "security.md"
    result = runner.invoke(
        app,
        ["preprocess", str(SECRETS), "--output", str(out), "--security-report", str(rep)],
    )
    assert result.exit_code == 0
    assert "high" in result.output  # summary warns about high-severity matches
    report_text = rep.read_text(encoding="utf-8")
    assert "Security scan" in report_text
    for secret in RAW_SECRETS:
        assert secret not in report_text


def test_cli_can_disable_scan(tmp_path: Path) -> None:
    out = tmp_path / "cleaned.json"
    result = runner.invoke(
        app, ["preprocess", str(SECRETS), "--output", str(out), "--no-security-scan"]
    )
    assert result.exit_code == 0
    assert "security scan" not in result.output.lower()


def test_report_location_does_not_leak_url_secrets() -> None:
    secret = "private-path-token"
    raw = {
        "log": {
            "entries": [
                {
                    "request": {
                        "url": f"https://user:{secret}@example.com/reset/{secret}#{secret}",
                        "headers": [{"name": "Authorization", "value": f"Bearer {secret}"}],
                    }
                }
            ]
        }
    }
    report = SecurityScanner().scan(raw)
    assert report.findings[0].location == "entry[0]"
    assert secret not in report.model_dump_json()
    assert secret not in report.to_markdown()
