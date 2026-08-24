"""Flat-file storage for a run: per-response JSON plus a side-by-side markdown index.

The ``index.md`` is the comparison surface the human reads when judging — every response,
grouped by prompt mode, with the cost/latency/token metadata alongside. No database.
"""

from __future__ import annotations

import json
from pathlib import Path

from harcompanon.execution import RunResponse, RunResult


def store_run(run: RunResult, out_dir: Path) -> Path:
    """Write the run under ``out_dir/<run_id>/`` and return that directory."""
    run_dir = out_dir / run.run_id
    responses_dir = run_dir / "responses"
    responses_dir.mkdir(parents=True, exist_ok=True)

    for item in run.responses:
        name = f"{item.provider}__{item.mode}.json"
        payload = item.model_dump(mode="json")
        (responses_dir / name).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    (run_dir / "run.json").write_text(run.model_dump_json(indent=2) + "\n", encoding="utf-8")
    (run_dir / "index.md").write_text(_index_markdown(run), encoding="utf-8")
    return run_dir


def load_run(run_dir: Path) -> RunResult:
    """Load a stored run back into a RunResult (from ``run.json``)."""
    run_json = run_dir / "run.json"
    if not run_json.is_file():
        raise ValueError(f"{run_dir} is not a run directory (no run.json).")
    return RunResult.model_validate_json(run_json.read_text(encoding="utf-8"))


def _fmt_cost(value: float | None) -> str:
    return f"${value:.4f}" if value is not None else "—"


def _fmt_int(value: int | None) -> str:
    return str(value) if value is not None else "—"


def _index_markdown(run: RunResult) -> str:
    lines = [
        f"# Run {run.run_id}",
        "",
        f"- **Fixture:** `{run.fixture}`",
        f"- **Created:** {run.created_at}",
        f"- **Dry run:** {'yes' if run.dry_run else 'no'}",
        f"- **Providers:** {', '.join(run.providers)}",
        f"- **Modes:** {', '.join(run.modes)}",
        "",
        "> The human is the sole judge. This index is a comparison surface, not a scoring.",
        "",
        "## Overview",
        "",
        "| Mode | Provider | Model | In tok | Out tok | Cost | Latency | Note |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in run.responses:
        r = item.response
        note = "error" if item.error else ("dry-run" if item.dry_run else "")
        latency = f"{r.latency_ms:.0f} ms" if r.latency_ms else "—"
        lines.append(
            f"| {item.mode} | {item.provider} | {r.model} | {_fmt_int(r.input_tokens)} "
            f"| {_fmt_int(r.output_tokens)} | {_fmt_cost(r.cost_usd)} | {latency} | {note} |"
        )

    lines.append("")
    lines.append("## Responses")
    for mode in run.modes:
        lines.append("")
        lines.append(f"### Mode: {mode}")
        for item in (i for i in run.responses if i.mode == mode):
            lines.extend(_response_section(item))
    return "\n".join(lines) + "\n"


def _response_section(item: RunResponse) -> list[str]:
    r = item.response
    out = ["", f"#### {item.provider} — {r.model}"]
    if item.error:
        out.append("")
        out.append(f"> **error:** {item.error}")
    out.append("")
    out.append(r.text if r.text else "_(empty)_")
    return out
