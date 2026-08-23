"""Load versioned prompt templates.

Prompts are DATA, not code: one file per (mode, version) under this package's ``prompts/``
directory, e.g. ``prompts/structured/v1.md``. Iterating on wording never touches pipeline
logic, and adding a mode is just adding a folder. A template's ``{{artifact}}`` placeholder
is replaced with the preprocessed evidence at render time.

Modes:
- ``minimal``    — bare probe; no role, no structure.
- ``briefed``    — assigns the instrument role + the session-based, pre-go-live situation.
- ``structured`` — role + situation + a required output structure (the only mode with a schema).
"""

from __future__ import annotations

import json
from importlib import resources
from importlib.resources.abc import Traversable
from typing import Any

ARTIFACT_PLACEHOLDER = "{{artifact}}"
_PACKAGE = "harcompanon"
_PROMPTS_DIR = "prompts"
_STRUCTURED_SPEC = "schemas/structured_response.schema.json"


def _prompts_root() -> Traversable:
    return resources.files(_PACKAGE) / _PROMPTS_DIR


def available_modes() -> list[str]:
    """List the prompt modes that have a template directory."""
    return sorted(entry.name for entry in _prompts_root().iterdir() if entry.is_dir())


def load_template(mode: str, version: str = "v1") -> str:
    """Return the raw template text for ``(mode, version)``."""
    template = _prompts_root() / mode / f"{version}.md"
    if not template.is_file():
        available = ", ".join(available_modes()) or "(none)"
        raise ValueError(
            f"No prompt template for mode={mode!r} version={version!r}. "
            f"Available modes: {available}."
        )
    return template.read_text(encoding="utf-8")


def render_prompt(mode: str, artifact_json: str, version: str = "v1") -> str:
    """Load a template and substitute the preprocessed evidence for its placeholder."""
    template = load_template(mode, version)
    if ARTIFACT_PLACEHOLDER not in template:
        raise ValueError(
            f"Template {mode}/{version} is missing the {ARTIFACT_PLACEHOLDER} placeholder."
        )
    return template.replace(ARTIFACT_PLACEHOLDER, artifact_json)


def load_structured_spec() -> dict[str, Any]:
    """Return the structural spec for the ``structured`` prompt's output.

    Consumed later by the structural check (post-processing): the required sections and
    per-finding fields the response should contain. A conformance spec, not a quality rubric.
    """
    spec_file = resources.files(_PACKAGE) / _STRUCTURED_SPEC
    return json.loads(spec_file.read_text(encoding="utf-8"))  # type: ignore[no-any-return]
