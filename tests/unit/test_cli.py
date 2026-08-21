"""Conventional software tests (pytest) for the CLI skeleton.

NB: these are *checks* on this codebase, unrelated to "testing" in the RST sense that
the tool itself is about.
"""

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
    for verb in ("preprocess", "run", "check", "judge", "closeout"):
        assert verb in result.stdout


def test_unbuilt_verb_exits_nonzero() -> None:
    result = runner.invoke(app, ["preprocess"])
    assert result.exit_code == 2
