"""Structural conformance check for structured responses — POST-PROCESSING, never a verdict.

This mechanically verifies that a ``structured`` response *has the shape the prompt asked for*:
the required sections, and per finding the Observation / Oracle / Status fields. It emits a
present/absent checklist. It says nothing about whether the findings are any *good* — that is
quality, and quality is judged by the human alone. Nothing here is AI-assisted or interpretive;
it is string presence only.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from harcompanon.execution import RunResponse, RunResult
from harcompanon.prompts import load_structured_spec


class SectionCheck(BaseModel):
    name: str
    present: bool


class FindingCheck(BaseModel):
    index: int
    title: str
    missing_fields: list[str]


class StructuralReport(BaseModel):
    """A mechanical present/absent checklist for one structured response. Not a quality score."""

    required_sections: list[SectionCheck]
    finding_fields: list[str]
    findings: list[FindingCheck]

    def all_sections_present(self) -> bool:
        return all(s.present for s in self.required_sections)

    def conforming_findings(self) -> int:
        return sum(1 for f in self.findings if not f.missing_fields)

    def conforms(self) -> bool:
        return (
            self.all_sections_present()
            and bool(self.findings)
            and self.conforming_findings() == len(self.findings)
        )


def _finding_blocks(text: str) -> list[tuple[str, str]]:
    """Return (title, body) for each ``### `` finding under the ``## Findings`` section."""
    blocks: list[tuple[str, str]] = []
    in_findings = False
    title: str | None = None
    body: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            if title is not None:
                blocks.append((title, "\n".join(body)))
                title, body = None, []
            in_findings = stripped.lower() == "## findings"
            continue
        if in_findings and stripped.startswith("### "):
            if title is not None:
                blocks.append((title, "\n".join(body)))
            title, body = stripped[4:].strip(), []
            continue
        if in_findings and title is not None:
            body.append(line)
    if title is not None:
        blocks.append((title, "\n".join(body)))
    return blocks


def check_structured(
    text: str, spec: dict[str, Any] | None = None, version: str = "v2"
) -> StructuralReport:
    """Mechanically check a structured response's shape against the spec for ``version``."""
    spec = spec or load_structured_spec(version)
    required_sections = [str(s) for s in spec.get("required_sections", [])]
    finding_fields = [str(f) for f in spec.get("finding_fields", [])]

    lowered = text.lower()
    sections = [
        SectionCheck(name=name, present=f"## {name}".lower() in lowered)
        for name in required_sections
    ]

    findings: list[FindingCheck] = []
    for index, (title, body) in enumerate(_finding_blocks(text), start=1):
        body_lower = body.lower()
        missing = [field for field in finding_fields if field.lower() not in body_lower]
        findings.append(FindingCheck(index=index, title=title, missing_fields=missing))

    return StructuralReport(
        required_sections=sections,
        finding_fields=finding_fields,
        findings=findings,
    )


def check_run(run: RunResult) -> list[tuple[RunResponse, StructuralReport]]:
    """Run the structural check over each *structured* response (other modes have no schema).

    Each response is checked against the spec for *its own* prompt version, so a v2 and a v3
    response in the same run are each judged by the shape their prompt actually asked for.
    """
    results: list[tuple[RunResponse, StructuralReport]] = []
    for item in run.responses:
        if item.mode == "structured":
            results.append((item, check_structured(item.response.text, version=item.version)))
    return results


def _tick(present: bool) -> str:
    return "x" if present else " "


def report_markdown(run: RunResult) -> str:
    """Render the structural checklist for a run's structured responses."""
    lines = [
        f"# Structural check — {run.run_id}",
        "",
        "> POST-PROCESSING: a mechanical present/absent check against the structured schema.",
        "> This is **not** a quality verdict — quality is judged by the human alone.",
        "",
    ]
    checked = check_run(run)
    if not checked:
        lines.append("_No `structured` responses in this run — nothing to check._")
        return "\n".join(lines) + "\n"

    for item, report in checked:
        lines.append(f"## {item.provider} — {item.model}")
        lines.append(f"Conforms: {'yes' if report.conforms() else 'no'}")
        lines.append("")
        lines.append("### Required sections")
        for section in report.required_sections:
            lines.append(f"- [{_tick(section.present)}] {section.name}")
        lines.append("")
        lines.append(
            f"### Findings ({report.conforming_findings()}/{len(report.findings)} conforming)"
        )
        if not report.findings:
            lines.append("- [ ] (no findings parsed)")
        for finding in report.findings:
            ok = not finding.missing_fields
            note = "all fields present" if ok else f"missing: {', '.join(finding.missing_fields)}"
            lines.append(f"- [{_tick(ok)}] {finding.index}. {finding.title} — {note}")
        lines.append("")
    return "\n".join(lines) + "\n"
