"""Conventional software tests (pytest) for the prompt loader.

Checks on our code — not "testing" in the RST sense.
"""

from __future__ import annotations

import pytest

from harcompanon.prompts import (
    ARTIFACT_PLACEHOLDER,
    available_modes,
    load_template,
    render_prompt,
)


def test_available_modes_are_minimal_and_structured() -> None:
    assert set(available_modes()) == {"minimal", "structured"}


def test_minimal_is_bare() -> None:
    text = load_template("minimal")
    assert "What do you notice?" in text  # neutral probe, not risk-primed
    # Bare: no role framing, no imposed structure.
    assert "session-based" not in text
    assert "## Findings" not in text


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
    for section in (
        "## Start here",
        "## Findings",
        "## Coverage and blind spots",
        "## Questions only a human can answer",
        "## Challenge your analysis",
    ):
        assert section in text
    # Required per-finding invariants; Oracle offered as a lens ("when useful").
    assert "Observation" in text and "Interpretation" in text and "Next investigation" in text
    assert "Oracle" in text
    # RST-safe framing: instrument, and the human is the judge.
    assert "instrument" in text and "human tester is the judge" in text
