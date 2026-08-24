"""Conventional software tests (pytest) for execution + storage, using a fake provider.

No API keys or network — a FakeProvider stands in for a real model, and --dry-run exercises
the pipeline with no provider call at all.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from harcompanon.cli import app
from harcompanon.execution import DRY_RUN_TEXT, run_benchmark
from harcompanon.providers import Provider, RawResponse
from harcompanon.storage import store_run

SAMPLE = Path(__file__).parents[1] / "data" / "sample.har"
runner = CliRunner()


class FakeProvider:
    name = "fake"
    model = "fake-1"

    def __init__(self, *, boom: bool = False) -> None:
        self.boom = boom

    def complete(self, prompt: str) -> RawResponse:
        if self.boom:
            raise RuntimeError("no network")
        return RawResponse(
            provider=self.name,
            model=self.model,
            text=f"seen {len(prompt)} chars",
            input_tokens=10,
            output_tokens=5,
            cost_usd=0.001,
            latency_ms=1.0,
        )


def test_fake_provider_satisfies_protocol() -> None:
    assert isinstance(FakeProvider(), Provider)


def test_run_calls_each_provider_and_mode() -> None:
    result = run_benchmark(SAMPLE, [FakeProvider()], ["minimal", "structured"])
    assert len(result.responses) == 2
    assert {r.mode for r in result.responses} == {"minimal", "structured"}
    for r in result.responses:
        assert r.error is None
        assert r.response.text.startswith("seen ")
        assert r.prompt_chars > 0


def test_dry_run_makes_no_call() -> None:
    result = run_benchmark(SAMPLE, [FakeProvider(boom=True)], ["minimal"], dry_run=True)
    # boom=True would raise if complete() were called — dry-run must skip it.
    assert result.responses[0].response.text == DRY_RUN_TEXT
    assert result.responses[0].error is None


def test_provider_error_is_captured_not_raised() -> None:
    result = run_benchmark(SAMPLE, [FakeProvider(boom=True)], ["minimal"])
    item = result.responses[0]
    assert item.error is not None
    assert "no network" in item.error
    assert item.response.text == ""


def test_store_run_writes_json_and_index(tmp_path: Path) -> None:
    result = run_benchmark(SAMPLE, [FakeProvider()], ["minimal", "structured"])
    run_dir = store_run(result, tmp_path)
    index = (run_dir / "index.md").read_text(encoding="utf-8")
    assert "### Mode: minimal" in index
    assert "### Mode: structured" in index
    assert "fake" in index
    saved = json.loads((run_dir / "responses" / "fake__minimal.json").read_text())
    assert saved["provider"] == "fake"
    assert saved["response"]["text"].startswith("seen ")


def test_cli_run_dry_run(tmp_path: Path) -> None:
    result = runner.invoke(app, ["run", str(SAMPLE), "--dry-run", "--out", str(tmp_path)])
    assert result.exit_code == 0, result.output
    run_dirs = list(tmp_path.iterdir())
    assert len(run_dirs) == 1
    assert (run_dirs[0] / "index.md").exists()


def test_cli_run_rejects_unknown_mode(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["run", str(SAMPLE), "--dry-run", "--modes", "bogus", "--out", str(tmp_path)]
    )
    assert result.exit_code == 2
    assert "Unknown mode" in result.output
