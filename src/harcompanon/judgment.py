"""Generate a low-friction human-judgment file for a run.

The human is the SOLE judge — this only *scaffolds* the judgment, it never scores. It produces
a pre-populated YAML form:

- **structured** responses: each finding is listed, parsed mechanically from the response's
  ``## Findings`` section (splitting on ``### `` headings). This is post-processing, not a
  verdict.
- **minimal / briefed** responses: presented WHOLE, with a single row telling the human to
  segment the findings themselves — an LLM splitting free-form prose into findings would be
  interpretation sneaking in.

For every finding the human fills: oracle named? defensible as your own? and where it lands
on the ladder (slop / plausible / provisional / validated).
"""

from __future__ import annotations

from harcompanon.execution import RunResponse, RunResult

LADDER = "slop | plausible | provisional | validated"
WHOLE_RESPONSE = "(whole response — segment the findings yourself)"


def structured_finding_titles(text: str) -> list[str]:
    """Mechanically pull each finding heading from a structured response's ## Findings section."""
    titles: list[str] = []
    in_findings = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_findings = stripped.lower() == "## findings"
            continue
        if in_findings and stripped.startswith("### "):
            titles.append(stripped[4:].strip())
    return titles


def _titles_for(item: RunResponse) -> list[str]:
    if item.mode == "structured" and not item.error:
        titles = structured_finding_titles(item.response.text)
        if titles:
            return titles
    return [WHOLE_RESPONSE]


def _yaml_str(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def generate_judgment(run: RunResult) -> str:
    """Return the judgment YAML form for ``run`` (the human fills the blank fields)."""
    lines = [
        f"# Human judgment — {run.run_id}",
        "# You are the sole judge. For each finding, fill in:",
        "#   oracle_named: yes|no       (does it rest on a nameable oracle?)",
        "#   defensible:   yes|no       (could you stand behind it as your own conclusion?)",
        f"#   ladder:       {LADDER}",
        "#   note:         free text",
        "# minimal/briefed responses are shown WHOLE — segment the findings yourself.",
        "",
        f"run_id: {_yaml_str(run.run_id)}",
        f"fixture: {_yaml_str(run.fixture)}",
        "responses:",
    ]
    for item in run.responses:
        lines.append(f"  - provider: {item.provider}")
        lines.append(f"    model: {_yaml_str(item.model)}")
        lines.append(f"    mode: {item.mode}")
        if item.error:
            lines.append(f"    error: {_yaml_str(item.error)}")
        lines.append("    findings:")
        for title in _titles_for(item):
            lines.append(f"      - title: {_yaml_str(title)}")
            lines.append("        oracle_named:")
            lines.append("        defensible:")
            lines.append("        ladder:")
            lines.append("        note:")
        lines.append("    holistic_note:")
    return "\n".join(lines) + "\n"
