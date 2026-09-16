"""CLI discovery and installed version smoke checks."""

from __future__ import annotations

from typer.testing import CliRunner

from harcompanon import __version__
from harcompanon.cli import app

runner = CliRunner()


def test_version_command_prints_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help_lists_pipeline_verbs() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for verb in ("preprocess", "redact", "pseudonymize", "run", "compare", "retry"):
        assert verb in result.stdout
