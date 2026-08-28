"""Tests for the HTML comparison matrix and its small markdown renderer."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from harcompanon.cli import app
from harcompanon.compare import compare_html, render_markdown
from harcompanon.execution import RunResponse, RunResult
from harcompanon.providers import RawResponse
from harcompanon.storage import store_run

runner = CliRunner()


def test_render_markdown_covers_the_used_subset() -> None:
    md = (
        "# Title\n\nA **bold** and `code` and *em*.\n\n"
        "- one\n- two\n\n"
        "| a | b |\n| --- | --- |\n| 1 | 2 |\n\n"
        "```\nx = 1\n```\n\n> a note\n"
    )
    out = render_markdown(md)
    assert "<h1>Title</h1>" in out
    assert "<strong>bold</strong>" in out and "<code>code</code>" in out and "<em>em</em>" in out
    assert "<ul><li>one</li><li>two</li></ul>" in out
    assert "<table>" in out and "<th>a</th>" in out and "<td>1</td>" in out
    assert "<pre><code>x = 1</code></pre>" in out
    assert "<blockquote>a note</blockquote>" in out


def test_render_markdown_escapes_html() -> None:
    out = render_markdown("a <script>alert(1)</script> b")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def _run() -> RunResult:
    def resp(provider: str, mode: str, text: str, error: str | None = None) -> RunResponse:
        return RunResponse(
            provider=provider,
            model=f"{provider}-1",
            mode=mode,
            version="v1",
            prompt_chars=10,
            dry_run=False,
            error=error,
            response=RawResponse(
                provider=provider, model=f"{provider}-1", text=text, latency_ms=1000.0
            ),
        )

    return RunResult(
        run_id="komoot_2models_2026-08-28_10-00-00",
        fixture="komoot.pseudo.har",
        created_at="2026-08-28T10:00:00+02:00",
        dry_run=False,
        providers=["anthropic", "openai"],
        modes=["minimal", "structured"],
        responses=[
            resp("anthropic", "minimal", "# Claude minimal\nfound X"),
            resp("openai", "minimal", "gpt minimal body"),
            resp("anthropic", "structured", "## Findings\n- one"),
            resp("openai", "structured", "", error="RateLimitError: 429"),
        ],
    )


def test_compare_html_is_a_matrix_with_all_cells() -> None:
    page = compare_html(_run())
    assert page.startswith("<!doctype html>")
    for token in ("anthropic", "openai", "minimal", "structured", "komoot.pseudo.har"):
        assert token in page
    assert "Claude minimal" in page and "gpt minimal body" in page
    assert "RateLimitError: 429" in page  # the errored cell surfaces its error
    assert "err-cell" in page
    # models are columns: 2 providers -> the grid repeats a fixed-width column twice
    assert "repeat(2,440px)" in page
    # a wider column width is honoured
    assert "repeat(2,700px)" in compare_html(_run(), col_px=700)


def test_cli_compare_writes_html(tmp_path: Path) -> None:
    run_dir = store_run(_run(), tmp_path)
    result = runner.invoke(app, ["compare", str(run_dir)])
    assert result.exit_code == 0, result.output
    assert (run_dir / "compare.html").is_file()
    assert "matrix" in result.output.lower()
