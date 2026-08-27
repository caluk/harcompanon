"""Conventional software tests (pytest) for the structural conformance check.

This verifies the mechanical present/absent check — including that it correctly *flags* missing
schema elements (success criterion 7). It says nothing about quality; neither does the code.
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from harcompanon.cli import app
from harcompanon.execution import RunResponse, RunResult
from harcompanon.providers import RawResponse
from harcompanon.structural_check import check_run, check_structured, report_markdown

SAMPLE = Path(__file__).parents[1] / "data" / "sample.har"
runner = CliRunner()

GOOD = (
    "## Findings\n"
    "### 1. Timezone mismatch\n- Observation — a\n- Oracle — b\n- Status — hypothesis\n"
    "### 2. Slow dashboard\n- Observation — a\n- Oracle — b\n- Status — hypothesis\n"
    "## Questions only a human can answer\n- ...\n"
    "## Self-critique\n- ...\n"
)


def test_well_formed_structured_response_conforms() -> None:
    report = check_structured(GOOD)
    assert report.all_sections_present()
    assert len(report.findings) == 2
    assert report.conforming_findings() == 2
    assert report.conforms()


def test_missing_section_is_flagged() -> None:
    without_selfcritique = GOOD.replace("## Self-critique\n- ...\n", "")
    report = check_structured(without_selfcritique)
    missing = [s.name for s in report.required_sections if not s.present]
    assert "Self-critique" in missing
    assert not report.conforms()


def test_missing_finding_field_is_flagged() -> None:
    no_oracle = GOOD.replace(
        "### 2. Slow dashboard\n- Observation — a\n- Oracle — b\n",
        "### 2. Slow dashboard\n- Observation — a\n",
    )
    report = check_structured(no_oracle)
    second = report.findings[1]
    assert "Oracle" in second.missing_fields
    assert not report.conforms()


def _run(structured_text: str) -> RunResult:
    def resp(mode: str, text: str) -> RunResponse:
        return RunResponse(
            provider="fake",
            model="fake-1",
            mode=mode,
            version="v1",
            prompt_chars=1,
            dry_run=False,
            error=None,
            response=RawResponse(provider="fake", model="fake-1", text=text),
        )

    return RunResult(
        run_id="r1",
        fixture="sample.har",
        created_at="2026-08-24T13:00:00+02:00",
        dry_run=False,
        providers=["fake"],
        modes=["minimal", "structured"],
        responses=[resp("minimal", "prose"), resp("structured", structured_text)],
    )


def test_check_run_only_checks_structured_responses() -> None:
    checked = check_run(_run(GOOD))
    assert len(checked) == 1  # minimal has no schema
    assert checked[0][0].mode == "structured"
    assert checked[0][1].conforms()


def test_report_markdown_is_post_processing_not_a_verdict() -> None:
    text = report_markdown(_run(GOOD))
    assert "POST-PROCESSING" in text
    assert "not** a quality verdict" in text
    assert "- [x] Findings" in text
    assert "Conforms: yes" in text


def test_cli_check_writes_checklist(tmp_path: Path) -> None:
    run_result = runner.invoke(app, ["run", str(SAMPLE), "--dry-run", "--out", str(tmp_path)])
    assert run_result.exit_code == 0, run_result.output
    run_dir = next(tmp_path.iterdir())
    checked = runner.invoke(app, ["check", str(run_dir)])
    assert checked.exit_code == 0, checked.output
    report = (run_dir / "structural_check.md").read_text(encoding="utf-8")
    assert "POST-PROCESSING" in report
    assert "not a verdict" in checked.output
