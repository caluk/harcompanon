"""Descriptive cross-run summary — indicators, NOT a verdict.

A thin aggregator over data we already compute: the structural check (findings, oracles
named, conformance) plus run metadata (tokens, cost, latency). It tabulates these across one
or many runs to help narrow fixtures and compare models. It deliberately does **no** quality
scoring and **no** LLM-as-judge — quality is judged by the human alone. Every number here is
descriptive; none of it ranks one response as "better".
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from harcompanon.execution import RunResponse, RunResult
from harcompanon.storage import load_run
from harcompanon.structural_check import check_structured


def _run_dirs(path: Path) -> list[Path]:
    """A path is either a run dir (has run.json) or a parent containing run dirs."""
    if (path / "run.json").is_file():
        return [path]
    return sorted({p.parent for p in path.glob("*/run.json")})


def load_runs(paths: list[Path]) -> list[RunResult]:
    dirs: list[Path] = []
    for path in paths:
        dirs.extend(_run_dirs(path))
    return [load_run(directory) for directory in dirs]


def _structured_metrics(item: RunResponse) -> tuple[int, int, str]:
    """(findings, oracles_named, conforms) for a structured response; blanks otherwise."""
    report = check_structured(item.response.text, version=item.version)
    findings = len(report.findings)
    oracles = sum(1 for finding in report.findings if "Oracle" not in finding.missing_fields)
    return findings, oracles, "yes" if report.conforms() else "no"


def _int(value: int | None) -> str:
    return str(value) if value is not None else "—"


def _cost(value: float | None) -> str:
    return f"${value:.4f}" if value is not None else "—"


def summarize(runs: list[RunResult]) -> str:
    """Render the descriptive summary markdown for the given runs."""
    lines = [
        "# Run summary",
        "",
        "> **Descriptive indicators, not a verdict.** These are mechanical counts (findings,",
        "> oracles named, conformance) and run metadata (tokens, cost, latency). They do not",
        "> score quality — quality is judged by the human alone.",
        "",
        f"Runs: {len(runs)}",
        "",
    ]
    columns = [
        "Fixture", "Mode", "Provider", "Model", "Findings", "Oracles",
        "Conforms", "In", "Out", "Cost", "Latency", "Note",
    ]  # fmt: skip
    lines.append("| " + " | ".join(columns) + " |")
    lines.append("| " + " | ".join("---" for _ in columns) + " |")
    # (fixture) -> [findings_total, oracles_total, conforming_count, structured_count]
    rollup: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])

    rows = sorted(
        ((run, item) for run in runs for item in run.responses),
        key=lambda pair: (pair[0].fixture, pair[1].mode, pair[1].provider),
    )
    for run, item in rows:
        r = item.response
        note = "error" if item.error else ("dry-run" if item.dry_run else "")
        if item.mode == "structured" and not item.error:
            findings, oracles, conforms = _structured_metrics(item)
            stats = rollup[run.fixture]
            stats[0] += findings
            stats[1] += oracles
            stats[2] += 1 if conforms == "yes" else 0
            stats[3] += 1
            f_cell, o_cell = str(findings), str(oracles)
        else:
            conforms, f_cell, o_cell = "—", "—", "—"
        latency = f"{r.latency_ms:.0f} ms" if r.latency_ms else "—"
        cells = [
            run.fixture, item.mode, item.provider, r.model, f_cell, o_cell, conforms,
            _int(r.input_tokens), _int(r.output_tokens), _cost(r.cost_usd), latency, note,
        ]  # fmt: skip
        lines.append("| " + " | ".join(cells) + " |")

    if rollup:
        lines.append("")
        lines.append("## Per-fixture (structured responses)")
        lines.append("")
        rollup_cols = [
            "Fixture", "Σ findings", "Σ oracles named", "Conforming", "Structured responses",
        ]  # fmt: skip
        lines.append("| " + " | ".join(rollup_cols) + " |")
        lines.append("| " + " | ".join("---" for _ in rollup_cols) + " |")
        for fixture in sorted(rollup):
            findings_total, oracles_total, conforming, structured = rollup[fixture]
            lines.append(
                f"| {fixture} | {findings_total} | {oracles_total} | {conforming} | {structured} |"
            )
    return "\n".join(lines) + "\n"
