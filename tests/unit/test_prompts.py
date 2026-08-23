"""Conventional software tests (pytest) for the prompt loader.

Checks on our code — not "testing" in the RST sense.
"""

from __future__ import annotations

import pytest

from harcompanon.prompts import (
    ARTIFACT_PLACEHOLDER,
    available_modes,
    load_structured_spec,
    load_template,
    render_prompt,
)


def test_available_modes_includes_the_three_tiers() -> None:
    modes = set(available_modes())
    assert {"minimal", "briefed", "structured"} <= modes


def test_minimal_is_bare() -> None:
    text = load_template("minimal")
    assert "What looks strange here?" in text
    # Bare: no role framing, no imposed structure.
    assert "session-based" not in text
    assert "## Findings" not in text


def test_briefed_has_role_and_situation_but_no_structure() -> None:
    text = load_template("briefed")
    assert "instrument" in text
    assert "session-based testing" in text
    assert "not the judge" in text
    assert "## " not in text  # no imposed section structure


def test_every_template_has_the_artifact_placeholder() -> None:
    for mode in available_modes():
        assert ARTIFACT_PLACEHOLDER in load_template(mode)


def test_render_substitutes_the_artifact() -> None:
    rendered = render_prompt("minimal", '{"calls": []}')
    assert ARTIFACT_PLACEHOLDER not in rendered
    assert '{"calls": []}' in rendered


def test_unknown_mode_raises_with_available_modes() -> None:
    with pytest.raises(ValueError, match="Available modes"):
        load_template("does-not-exist")


def test_unknown_version_raises() -> None:
    with pytest.raises(ValueError, match="version"):
        load_template("minimal", "v999")


def test_structured_has_required_sections_and_oracle() -> None:
    text = load_template("structured")
    for section in ("## Findings", "## Questions only a human can answer", "## Self-critique"):
        assert section in text
    assert "Oracle" in text
    assert "hypotheses, not findings" in text
    # RST-safe framing: instrument, not the tester/judge.
    assert "not the tester" in text


def test_structured_spec_matches_the_template() -> None:
    # The spec the structural check will use must line up with the actual template.
    spec = load_structured_spec()
    text = load_template("structured")
    for section in spec["required_sections"]:
        assert f"## {section}" in text
    for field in spec["finding_fields"]:
        assert field in text
