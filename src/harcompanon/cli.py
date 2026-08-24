"""Command-line entry point for harcompañon.

The pipeline is intentionally split into small, composable verbs. Each verb below is
a stub for now; the real behaviour arrives with its tracked Beans task (id in the
message). Nothing here judges response quality — judging is the human's job. Any verb
that touches model output does so only as mechanical *post-processing*.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from harcompanon import __version__
from harcompanon.closeout import generate_closeout
from harcompanon.config import build_provider, load_credentials
from harcompanon.execution import run_benchmark
from harcompanon.judgment import generate_judgment
from harcompanon.preprocess import SecurityScanner, load_har, preprocess_har
from harcompanon.prompts import available_modes
from harcompanon.redact import redact_file
from harcompanon.storage import load_run, store_run
from harcompanon.structural_check import check_run, report_markdown

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Compare LLMs as RST testing companions on the same frozen evidence and prompt.",
)


@app.command()
def version() -> None:
    """Print the installed harcompañon version."""
    typer.echo(__version__)


@app.command()
def preprocess(
    har: Annotated[
        Path,
        typer.Argument(
            exists=True,
            dir_okay=False,
            readable=True,
            help="Path to the HAR file to preprocess.",
        ),
    ],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write the cleaned JSON here (default: stdout)."),
    ] = None,
    security_report: Annotated[
        Path | None,
        typer.Option("--security-report", help="Write the full masked security report here."),
    ] = None,
    security_scan: Annotated[
        bool,
        typer.Option(
            "--security-scan/--no-security-scan",
            help="Scan the raw HAR for secrets/PII and warn (safety guardrail).",
        ),
    ] = True,
) -> None:
    """Strip a HAR down to its JSON API calls (mechanical noise removal only)."""
    raw = load_har(har)
    artifact = preprocess_har(raw, source_har=har.name)
    payload = artifact.to_canonical_json()

    if output is None:
        typer.echo(payload, nl=False)
    else:
        output.write_text(payload, encoding="utf-8")
        typer.secho(
            f"Kept {len(artifact.calls)}/{artifact.total_entries} call envelopes "
            f"({artifact.json_body_count} with JSON bodies) -> {output}",
            fg=typer.colors.GREEN,
            err=True,
        )

    # Safety guardrail: mechanical secrets/PII scan of the RAW HAR (what gets committed).
    # Reported separately; it never touches the cleaned evidence above.
    if security_scan:
        report = SecurityScanner().scan(raw, source_har=har.name)
        colour = (
            typer.colors.RED
            if report.has_high()
            else (typer.colors.YELLOW if report.has_findings() else typer.colors.GREEN)
        )
        typer.secho(report.summary_line(), fg=colour, err=True)
        if security_report is not None:
            security_report.write_text(report.to_markdown(), encoding="utf-8")
            typer.secho(f"Security report -> {security_report}", fg=colour, err=True)


@app.command()
def redact(
    har: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, readable=True, help="HAR file to redact."),
    ],
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write here (default: <name>.redacted.har)."),
    ] = None,
) -> None:
    """Mask scanner-detected secrets in a HAR, producing a safe-to-commit-and-send copy."""
    dest = output or har.with_name(f"{har.stem}.redacted.har")
    removed, remaining = redact_file(har, dest)
    typer.secho(
        f"Redacted {removed} secret value occurrence(s) -> {dest}",
        fg=typer.colors.GREEN,
        err=True,
    )
    if remaining == 0:
        typer.secho(
            "Verified: no detected secret value remains "
            "(sensitive header/field NAMES stay; only values are removed).",
            fg=typer.colors.GREEN,
            err=True,
        )
    else:
        typer.secho(
            f"WARNING: {remaining} secret occurrence(s) still present — review manually.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)


@app.command()
def run(
    fixture: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, readable=True, help="HAR fixture to run."),
    ],
    providers: Annotated[
        list[str] | None,
        typer.Option("--provider", "-p", help="Provider name (repeatable). Default: anthropic."),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", help="Override the model id for all providers."),
    ] = None,
    modes: Annotated[
        str,
        typer.Option("--modes", help="Comma-separated prompt modes."),
    ] = "minimal,briefed,structured",
    out: Annotated[
        Path,
        typer.Option("--out", "-o", help="Directory to write the run into."),
    ] = Path("runs"),
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run/--live", help="Render prompts without calling any API."),
    ] = False,
) -> None:
    """Run one fixture across the chosen providers x prompt modes (stateless API calls)."""
    mode_list = [m.strip() for m in modes.split(",") if m.strip()]
    known = set(available_modes())
    unknown = [m for m in mode_list if m not in known]
    if unknown:
        typer.secho(
            f"Unknown mode(s): {', '.join(unknown)}. Available: {', '.join(sorted(known))}.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=2)

    provider_names = providers or ["anthropic"]
    if not dry_run:
        load_credentials()
    built = [build_provider(name, model) for name in provider_names]

    result = run_benchmark(fixture, built, mode_list, dry_run=dry_run)
    run_dir = store_run(result, out)

    errors = sum(1 for r in result.responses if r.error)
    total_cost = sum(r.response.cost_usd or 0.0 for r in result.responses)
    typer.secho(
        f"{'[dry-run] ' if dry_run else ''}{len(result.responses)} responses "
        f"({errors} error(s)) -> {run_dir}",
        fg=typer.colors.RED if errors else typer.colors.GREEN,
        err=True,
    )
    if not dry_run and total_cost:
        typer.secho(f"Total cost: ${total_cost:.4f}", fg=typer.colors.GREEN, err=True)


@app.command()
def check(
    run_dir: Annotated[
        Path,
        typer.Argument(exists=True, file_okay=False, help="A run directory (contains run.json)."),
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output", "-o", help="Write the checklist here (default: <run>/structural_check.md)."
        ),
    ] = None,
) -> None:
    """Post-processing: structural conformance check of structured responses (not a verdict)."""
    run = load_run(run_dir)
    dest = output or (run_dir / "structural_check.md")
    dest.write_text(report_markdown(run), encoding="utf-8")
    checked = check_run(run)
    conforming = sum(1 for _, report in checked if report.conforms())
    typer.secho(
        f"Structural check: {conforming}/{len(checked)} structured responses conform "
        f"(mechanical presence check, not a verdict) -> {dest}",
        fg=typer.colors.GREEN,
        err=True,
    )


@app.command()
def judge(
    run_dir: Annotated[
        Path,
        typer.Argument(exists=True, file_okay=False, help="A run directory (contains run.json)."),
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output", "-o", help="Write the judgment YAML here (default: <run>/judgment.yml)."
        ),
    ] = None,
) -> None:
    """Generate the human-judgment file for a run (you fill it in; you are the judge)."""
    run = load_run(run_dir)
    dest = output or (run_dir / "judgment.yml")
    dest.write_text(generate_judgment(run), encoding="utf-8")
    typer.secho(
        f"Judgment form -> {dest} (you are the sole judge)", fg=typer.colors.GREEN, err=True
    )


@app.command()
def closeout(
    run_dir: Annotated[
        Path,
        typer.Argument(exists=True, file_okay=False, help="A run directory (contains run.json)."),
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output", "-o", help="Write the close-out here (default: <run>/closeout.md)."
        ),
    ] = None,
) -> None:
    """Generate a session close-out scaffold from the five debrief questions."""
    run = load_run(run_dir)
    dest = output or (run_dir / "closeout.md")
    dest.write_text(generate_closeout(run), encoding="utf-8")
    typer.secho(f"Close-out scaffold -> {dest}", fg=typer.colors.GREEN, err=True)


if __name__ == "__main__":
    app()
