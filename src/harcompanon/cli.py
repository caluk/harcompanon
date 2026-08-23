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
from harcompanon.preprocess import SecurityScanner, load_har, preprocess_har

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Compare LLMs as RST testing companions on the same frozen evidence and prompt.",
)


def _not_implemented(verb: str, bean: str) -> None:
    """Report an unbuilt verb honestly and exit non-zero (tracked by a Beans task)."""
    typer.secho(
        f"`{verb}` is not implemented yet (tracked by {bean}).",
        fg=typer.colors.YELLOW,
        err=True,
    )
    raise typer.Exit(code=2)


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
def run() -> None:
    """Run one fixture across all providers x both prompts (stateless API calls)."""
    _not_implemented("run", "harcompanon-zdym")


@app.command()
def check() -> None:
    """Post-processing: structural conformance check of structured responses (never a verdict)."""
    _not_implemented("check", "harcompanon-fvt4")


@app.command()
def judge() -> None:
    """Generate the low-friction human-judgment file for a run (the human fills it in)."""
    _not_implemented("judge", "harcompanon-kx8f")


@app.command()
def closeout() -> None:
    """Generate a session close-out scaffold from the five debrief questions."""
    _not_implemented("closeout", "harcompanon-s053")


if __name__ == "__main__":
    app()
