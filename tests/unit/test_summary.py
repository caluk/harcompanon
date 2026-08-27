"""Conventional software tests (pytest) for the descriptive cross-run summary."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from harcompanon.cli import app
from harcompanon.execution import RunResponse, RunResult
from harcompanon.providers import RawResponse
from harcompanon.storage import store_run
from harcompanon.summary import load_runs, summarize

SAMPLE = Path(__file__).parents[1] / "data" / "sample.har"
runner = CliRunner()

STRUCTURED = (
    "## Findings\n"
    "### 1. A\n- Observation — x\n- Oracle — y\n- Status — hypothesis\n"
    "### 2. B\n- Observation — x\n- Oracle — y\n- Status — hypothesis\n"
    "## Questions only a human can answer\n- q\n"
    "## Self-critique\n- s\n"
)


def _run(fixture: str, structured_text: str, cost: float | None = 0.05) -> RunResult:
    def resp(mode: str, text: str) -> RunResponse:
        return RunResponse(
            provider="fake",
            model="fake-1",
            mode=mode,
            version="v1",
            prompt_chars=1,
            dry_run=False,
            error=None,
            response=RawResponse(
                provider="fake",
                model="fake-1",
                text=text,
                input_tokens=100,
                output_tokens=50,
                cost_usd=cost,
                latency_ms=1200.0,
            ),
        )

    return RunResult(
        run_id=f"{fixture}_fake-1_2026-08-25_10-00-00",
        fixture=fixture,
        created_at="2026-08-25T10:00:00+02:00",
        dry_run=False,
        providers=["fake"],
        modes=["minimal", "structured"],
        responses=[resp("minimal", "prose"), resp("structured", structured_text)],
    )


def test_summarize_counts_findings_and_oracles() -> None:
    text = summarize([_run("sample.har", STRUCTURED)])
    assert "Descriptive indicators, not a verdict" in text
    # structured row: 2 findings, 2 oracles named, conforms yes
    assert "| sample.har | structured | fake | fake-1 | 2 | 2 | yes |" in text
    # minimal row shows blanks for the structured-only metrics
    assert "| sample.har | minimal | fake | fake-1 | — | — | — |" in text
    # per-fixture rollup present
    assert "## Per-fixture (structured responses)" in text
    assert "| sample.har | 2 | 2 | 1 | 1 |" in text


def test_load_runs_from_parent_dir(tmp_path: Path) -> None:
    store_run(_run("sample.har", STRUCTURED), tmp_path)
    store_run(_run("other.har", STRUCTURED), tmp_path)
    runs = load_runs([tmp_path])
    assert len(runs) == 2
    assert {r.fixture for r in runs} == {"sample.har", "other.har"}


def test_cli_summary(tmp_path: Path) -> None:
    # Produce a run, then summarise the parent directory.
    runner.invoke(app, ["run", str(SAMPLE), "--dry-run", "--out", str(tmp_path)])
    result = runner.invoke(app, ["summary", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "Descriptive indicators" in result.output
    assert "Runs: 1" in result.output


def test_cli_summary_no_runs(tmp_path: Path) -> None:
    result = runner.invoke(app, ["summary", str(tmp_path)])
    assert result.exit_code == 2
    assert "No runs found" in result.output
