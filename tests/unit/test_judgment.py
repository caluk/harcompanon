"""Conventional software tests (pytest) for the judgment + close-out generators and run I/O."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from harcompanon.cli import app
from harcompanon.closeout import generate_closeout
from harcompanon.execution import RunResponse, RunResult
from harcompanon.judgment import WHOLE_RESPONSE, generate_judgment, structured_finding_titles
from harcompanon.providers import RawResponse
from harcompanon.storage import load_run, store_run

SAMPLE = Path(__file__).parents[1] / "data" / "sample.har"
runner = CliRunner()

STRUCTURED_TEXT = (
    "## Findings\n"
    "### 1. Timezone mismatch\n- Observation ...\n- Oracle ...\n"
    "### 2. Slow dashboard\n- Observation ...\n"
    "## Questions only a human can answer\n- ...\n"
    "## Self-critique\n- ...\n"
)


def _response(mode: str, text: str, cost: float | None = None) -> RunResponse:
    return RunResponse(
        provider="fake",
        model="fake-1",
        mode=mode,
        version="v1",
        prompt_chars=10,
        dry_run=False,
        error=None,
        response=RawResponse(provider="fake", model="fake-1", text=text, cost_usd=cost),
    )


def _run() -> RunResult:
    return RunResult(
        run_id="dash_fake-1_2026-08-24_13-11-56",
        fixture="sample.har",
        created_at="2026-08-24T13:11:56+02:00",
        dry_run=False,
        providers=["fake"],
        modes=["minimal", "structured"],
        responses=[
            _response("minimal", "Free-form prose about what looks strange."),
            _response("structured", STRUCTURED_TEXT, cost=0.02),
        ],
    )


def test_structured_finding_titles_parses_headings() -> None:
    assert structured_finding_titles(STRUCTURED_TEXT) == [
        "1. Timezone mismatch",
        "2. Slow dashboard",
    ]
    # Headings outside the Findings section are ignored.
    assert structured_finding_titles("## Self-critique\n### not a finding\n") == []


def test_judgment_lists_structured_findings_and_whole_minimal() -> None:
    text = generate_judgment(_run())
    assert "1. Timezone mismatch" in text
    assert "2. Slow dashboard" in text
    assert WHOLE_RESPONSE in text  # minimal is presented whole
    for field in ("oracle_named:", "defensible:", "ladder:", "note:", "holistic_note:"):
        assert field in text
    assert "slop | plausible | provisional | validated" in text


def test_closeout_has_the_five_questions_and_metadata() -> None:
    text = generate_closeout(_run())
    for heading in (
        "## 1. What did you do?",
        "## 2. How did it go?",
        "## 3. Did you notice specific problems?",
        "## 4. How did you evaluate them?",
        "## 5. Now what?",
    ):
        assert heading in text
    assert "sample.har" in text
    assert "$0.0200" in text  # total cost from the structured response


def test_store_and_load_run_round_trip(tmp_path: Path) -> None:
    run = _run()
    run_dir = store_run(run, tmp_path)
    assert (run_dir / "run.json").exists()
    loaded = load_run(run_dir)
    assert loaded.run_id == run.run_id
    assert [r.mode for r in loaded.responses] == ["minimal", "structured"]


def test_load_run_rejects_non_run_dir(tmp_path: Path) -> None:
    import pytest

    with pytest.raises(ValueError, match="not a run directory"):
        load_run(tmp_path)


def test_cli_judge_and_closeout(tmp_path: Path) -> None:
    run_result = runner.invoke(app, ["run", str(SAMPLE), "--dry-run", "--out", str(tmp_path)])
    assert run_result.exit_code == 0, run_result.output
    run_dir = next(tmp_path.iterdir())

    judged = runner.invoke(app, ["judge", str(run_dir)])
    assert judged.exit_code == 0, judged.output
    assert (run_dir / "judgment.yml").exists()

    closed = runner.invoke(app, ["closeout", str(run_dir)])
    assert closed.exit_code == 0, closed.output
    assert "## 5. Now what?" in (run_dir / "closeout.md").read_text(encoding="utf-8")
