"""Versioned prompts must load and preserve the supplied evidence verbatim."""

from __future__ import annotations

import pytest

from harcompanon.prompts import ARTIFACT_PLACEHOLDER, load_template, render_prompt


@pytest.mark.parametrize("mode", ["minimal", "structured"])
@pytest.mark.parametrize("version", ["v1", "v2", "v3", "v4", "v5"])
def test_render_preserves_template_and_evidence(mode: str, version: str) -> None:
    template = load_template(mode, version)
    assert template.count(ARTIFACT_PLACEHOLDER) == 1
    before, after = template.split(ARTIFACT_PLACEHOLDER)
    artifact = '{"calls": [], "literal": "{{artifact}} <script> & é"}'
    assert render_prompt(mode, artifact, version) == before + artifact + after


@pytest.mark.parametrize(
    ("mode", "version", "message"),
    [("does-not-exist", "v5", "Available modes"), ("minimal", "v999", "version")],
)
def test_unknown_template_raises(mode: str, version: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        load_template(mode, version)
