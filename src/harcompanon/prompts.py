"""Load versioned prompt templates.

Prompts are DATA, not code: one file per (mode, version) under this package's ``prompts/``
directory, e.g. ``prompts/structured/v1.md``. Iterating on wording never touches pipeline
logic, and adding a mode is just adding a folder. A template's ``{{artifact}}`` placeholder
is replaced with the preprocessed evidence at render time.

Modes:
- ``minimal``    — bare probe; no role, no structure.
- ``structured`` — role + situation + a required output structure.
"""

from __future__ import annotations

from importlib import resources
from importlib.resources.abc import Traversable

ARTIFACT_PLACEHOLDER = "{{artifact}}"
_PACKAGE = "harcompanon"
_PROMPTS_DIR = "prompts"


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
