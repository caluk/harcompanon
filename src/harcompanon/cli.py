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
from harcompanon.preprocess import preprocess_file

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
) -> None:
    """Strip a HAR down to its JSON API calls (mechanical noise removal only)."""
    artifact = preprocess_file(har)
    payload = artifact.to_canonical_json()
    if output is None:
        typer.echo(payload, nl=False)
        return
    output.write_text(payload, encoding="utf-8")
    typer.secho(
        f"Kept {artifact.kept_entries}/{artifact.total_entries} calls -> {output}",
        fg=typer.colors.GREEN,
        err=True,
    )


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
