"""Mechanical HAR preprocessing: strip a HAR down to its JSON API calls.

Noise removal only — never interpretation or highlighting.
"""

from __future__ import annotations

from pathlib import Path

from harcompanon.models import CleanedArtifact
from harcompanon.preprocess.har import load_har, preprocess_har
from harcompanon.preprocess.rules import NoiseRules


def preprocess_file(path: Path, rules: NoiseRules | None = None) -> CleanedArtifact:
    """Load a HAR file and return its CleanedArtifact."""
    return preprocess_har(load_har(path), rules, source_har=path.name)


__all__ = ["NoiseRules", "load_har", "preprocess_file", "preprocess_har"]
