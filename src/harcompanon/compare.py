"""Render a run as a self-contained HTML comparison matrix — models x prompt modes.

Each cell is a scrollable panel with the response rendered from markdown, plus a compact
metadata header (model, tokens, reasoning, latency). Reading *across a row* compares models
on the same prompt; reading *down a column* compares a model's prompt modes.

This only lays the responses out — it never scores them. The page is a single
file with inlined CSS (no external assets), so it opens straight in a browser and is theme-aware.

The markdown renderer is a small dependency-free subset covering exactly what the responses use:
fenced code, pipe tables, headings, lists, blockquotes, horizontal rules, and inline
bold/italic/code. It is deliberately not a full CommonMark implementation.
"""

from __future__ import annotations

import html
import re

from harcompanon.execution import RunResponse, RunResult

_BLOCK_START = re.compile(r"^\s*(#{1,6}\s|[-*+]\s|\d+\.\s|>|```|([-*_])\2\2)")


def _inline(text: str) -> str:
    """Inline formatting on already-block-split text: code spans, bold, italic."""
    parts = re.split(r"(`[^`]+`)", text)
    out: list[str] = []
    for part in parts:
        if len(part) >= 2 and part.startswith("`") and part.endswith("`"):
            out.append(f"<code>{html.escape(part[1:-1], quote=False)}</code>")
            continue
        escaped = html.escape(part, quote=False)
        escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)
        out.append(escaped)
    return "".join(out)


def _cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def render_markdown(md: str) -> str:
    """Render the markdown subset the responses use to a safe HTML fragment."""
    lines = md.split("\n")
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if line.strip().startswith("```"):  # fenced code
            i += 1
            code: list[str] = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1  # closing fence
            out.append(f"<pre><code>{html.escape(chr(10).join(code), quote=False)}</code></pre>")
        elif (
            "|" in line
            and i + 1 < n
            and "-" in lines[i + 1]
            and re.fullmatch(r"[\s:|-]+", lines[i + 1])
        ):  # pipe table (header row + --- separator)
            header = _cells(line)
            i += 2
            body: list[list[str]] = []
            while i < n and "|" in lines[i] and lines[i].strip():
                body.append(_cells(lines[i]))
                i += 1
            head_html = "".join(f"<th>{_inline(c)}</th>" for c in header)
            rows_html = "".join(
                "<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in body
            )
            out.append(
                f"<table><thead><tr>{head_html}</tr></thead><tbody>{rows_html}</tbody></table>"
            )
        elif m := re.match(r"^(#{1,6})\s+(.*)$", line):
            level = len(m.group(1))
            out.append(f"<h{level}>{_inline(m.group(2))}</h{level}>")
            i += 1
        elif re.fullmatch(r"\s*([-*_])\1\1+\s*", line):  # horizontal rule
            out.append("<hr>")
            i += 1
        elif line.strip().startswith(">"):  # blockquote
            quote: list[str] = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append(f"<blockquote>{_inline(' '.join(quote))}</blockquote>")
        elif re.match(r"^\s*[-*+]\s+", line):  # unordered list
            items: list[str] = []
            while i < n and re.match(r"^\s*[-*+]\s+", lines[i]):
                items.append(_inline(re.sub(r"^\s*[-*+]\s+", "", lines[i])))
                i += 1
            out.append("<ul>" + "".join(f"<li>{it}</li>" for it in items) + "</ul>")
        elif re.match(r"^\s*\d+\.\s+", line):  # ordered list
            ol: list[str] = []
            while i < n and re.match(r"^\s*\d+\.\s+", lines[i]):
                ol.append(_inline(re.sub(r"^\s*\d+\.\s+", "", lines[i])))
                i += 1
            out.append("<ol>" + "".join(f"<li>{it}</li>" for it in ol) + "</ol>")
        elif not line.strip():
            i += 1
        else:  # paragraph — gather until a blank line or a new block starts
            para = [line]
            i += 1
            while i < n and lines[i].strip() and not _BLOCK_START.match(lines[i]):
                para.append(lines[i])
                i += 1
            out.append(f"<p>{_inline(' '.join(para))}</p>")
    return "\n".join(out)


def _meta(item: RunResponse) -> str:
    if item.error:
        return f'<span class="err">error: {html.escape(item.error[:120])}</span>'
    r = item.response
    bits = [html.escape(r.model)]
    if r.input_tokens or r.output_tokens:
        bits.append(f"{r.input_tokens or '—'}/{r.output_tokens or '—'} tok")
    if r.reasoning_tokens:
        bits.append(f"{r.reasoning_tokens} reasoning")
    if r.latency_ms:
        bits.append(f"{r.latency_ms / 1000:.1f}s")
    return " · ".join(bits)


def compare_html(run: RunResult, col_px: int = 440) -> str:
    """Build the self-contained HTML page: models as columns, modes as rows.

    Reading *across a row* compares all models on the same prompt (scroll horizontally through
    them); reading *down a column* compares a model's prompt modes. Columns are a fixed width so
    the grid scrolls sideways — ``col_px`` (default 440) fits ~3 columns on a 14" laptop.
    """
    by = {(item.provider, item.mode): item for item in run.responses}
    nproviders = len(run.providers)

    header = "".join(f"<div class='col-head'>{html.escape(p)}</div>" for p in run.providers)
    grid_rows = [f"<div class='corner'>{html.escape(run.fixture)}</div>{header}"]
    for mode in run.modes:
        cells = [f"<div class='row-head'>{html.escape(mode)}</div>"]
        for provider in run.providers:
            item = by.get((provider, mode))
            if item is None:
                cells.append("<div class='cell'><div class='body muted'>—</div></div>")
                continue
            klass = "cell err-cell" if item.error else "cell"
            body = render_markdown(item.response.text) if item.response.text else "<p>—</p>"
            cells.append(
                f"<div class='{klass}'><div class='meta'>{_meta(item)}</div>"
                f"<div class='body'>{body}</div></div>"
            )
        grid_rows.append("".join(cells))

    grid = "".join(f"<div class='grid-row'>{row}</div>" for row in grid_rows)
    return (
        _PAGE.replace("__TITLE__", html.escape(run.run_id))
        .replace("__NCOL__", str(nproviders))
        .replace("__COL__", str(col_px))
        .replace("__GRID__", grid)
    )


_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{
--bg:#fff;--fg:#1a1a1a;--muted:#666;--line:#e2e2e2;
--head:#f5f5f5;--err:#b00020;--code:#f0f0f0}
@media(prefers-color-scheme:dark){:root{
--bg:#141414;--fg:#e8e8e8;--muted:#9a9a9a;--line:#333;
--head:#1e1e1e;--err:#ff6b81;--code:#222}}
*{box-sizing:border-box}
body{margin:0;color:var(--fg);background:var(--bg);
font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
h1{font-size:15px;font-weight:600;margin:0;padding:10px 14px;border-bottom:1px solid var(--line)}
.note{color:var(--muted);font-weight:400}
.grid{overflow:auto;max-height:calc(100vh - 46px)}
.grid-row{display:grid;grid-template-columns:120px repeat(__NCOL__,__COL__px);width:max-content}
.col-head,.corner,.row-head{
position:sticky;background:var(--head);font-weight:600;padding:8px 10px;
border-bottom:1px solid var(--line);border-right:1px solid var(--line)}
.col-head{top:0;text-align:center;z-index:2}
.corner{top:0;left:0;z-index:4}
.row-head{left:0;display:flex;align-items:center;z-index:3}
.cell{border-bottom:1px solid var(--line);border-right:1px solid var(--line);
max-height:calc(100vh - 92px);overflow:auto;padding:0 12px 12px}
.err-cell{background:color-mix(in srgb,var(--err) 8%,transparent)}
.meta{position:sticky;top:0;background:var(--bg);color:var(--muted);font-size:12px;
padding:6px 0;border-bottom:1px solid var(--line);margin-bottom:8px}
.err{color:var(--err)}
.body{font-size:13.5px;word-wrap:break-word;overflow-wrap:anywhere}
.body.muted{color:var(--muted)}
.body h1,.body h2,.body h3,.body h4{font-size:14px;margin:14px 0 6px;padding:0;border:0}
.body h1{font-size:15px}
.body pre{background:var(--code);padding:8px;border-radius:4px;overflow-x:auto}
.body code{background:var(--code);padding:1px 4px;border-radius:3px;font-size:12px}
.body pre code{padding:0;background:transparent}
.body table{border-collapse:collapse;width:100%;font-size:12.5px;margin:8px 0}
.body th,.body td{border:1px solid var(--line);padding:4px 6px;text-align:left;vertical-align:top}
.body th{background:var(--head)}
.body blockquote{margin:8px 0;padding:2px 10px;border-left:3px solid var(--line);color:var(--muted)}
.body ul,.body ol{padding-left:20px;margin:6px 0}
</style></head>
<body>
<h1>__TITLE__ &nbsp;<span class="note">— response comparison.
The human is the sole judge.</span></h1>
<div class="grid">__GRID__</div>
</body></html>
"""
