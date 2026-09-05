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
#: The v2 spec keeps the original, unversioned filename (it is the committed study's schema);
#: later versions live alongside it as ``structured_response.<version>.schema.json``.
_STRUCTURED_SPEC = "schemas/structured_response.schema.json"
_STRUCTURED_SPEC_VERSIONED = "schemas/structured_response.{version}.schema.json"


def _prompts_root() -> Traversable:
    return resources.files(_PACKAGE) / _PROMPTS_DIR


def available_modes() -> list[str]:
    """List the prompt modes that have a template directory."""
    return sorted(entry.name for entry in _prompts_root().iterdir() if entry.is_dir())


def load_template(mode: str, version: str = "v2") -> str:
    """Return the raw template text for ``(mode, version)``."""
    template = _prompts_root() / mode / f"{version}.md"
    if not template.is_file():
        available = ", ".join(available_modes()) or "(none)"
        raise ValueError(
            f"No prompt template for mode={mode!r} version={version!r}. "
            f"Available modes: {available}."
        )
    return template.read_text(encoding="utf-8")


def render_prompt(mode: str, artifact_json: str, version: str = "v2") -> str:
    """Load a template and substitute the preprocessed evidence for its placeholder."""
    template = load_template(mode, version)
    if ARTIFACT_PLACEHOLDER not in template:
        raise ValueError(
            f"Template {mode}/{version} is missing the {ARTIFACT_PLACEHOLDER} placeholder."
        )
    return template.replace(ARTIFACT_PLACEHOLDER, artifact_json)


def load_structured_spec(version: str = "v2") -> dict[str, Any]:
    """Return the structural spec for the ``structured`` prompt's output at ``version``.

    Consumed later by the structural check (post-processing): the required sections and
    per-finding fields the response should contain. A conformance spec, not a quality rubric.
    A structured prompt version may bring its own spec when its section architecture changes
    (v3 renames ``Start here`` to ``Overall picture`` and adds an optional ``Systemic
    observations`` section). ``v2`` keeps the original unversioned filename, and any version
    without a dedicated spec falls back to it — matching the historical behaviour when the check
    was version-agnostic.
    """
    spec_file = resources.files(_PACKAGE) / _STRUCTURED_SPEC_VERSIONED.format(version=version)
    if not spec_file.is_file():
        spec_file = resources.files(_PACKAGE) / _STRUCTURED_SPEC  # fall back to the v2 baseline
    return json.loads(spec_file.read_text(encoding="utf-8"))  # type: ignore[no-any-return]
