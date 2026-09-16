"""Mechanical HAR preprocessing: keep call envelopes and JSON bodies.

Noise removal only — never interpretation or highlighting.
"""

from __future__ import annotations

from pathlib import Path

from harcompanon.models import CleanedArtifact
from harcompanon.preprocess.har import load_har, preprocess_har
from harcompanon.preprocess.rules import NoiseRules
from harcompanon.preprocess.security import (
    SecurityFinding,
    SecurityReport,
    SecurityScanner,
    Severity,
)


def preprocess_file(path: Path, rules: NoiseRules | None = None) -> CleanedArtifact:
    """Load a HAR file and return its CleanedArtifact."""
    return preprocess_har(load_har(path), rules, source_har=path.name)


def scan_file(path: Path, scanner: SecurityScanner | None = None) -> SecurityReport:
    """Load a HAR file and run the mechanical secrets/PII scan over the raw contents."""
    return (scanner or SecurityScanner()).scan(load_har(path), source_har=path.name)


__all__ = [
    "NoiseRules",
    "SecurityFinding",
    "SecurityReport",
    "SecurityScanner",
    "Severity",
    "load_har",
    "preprocess_file",
    "preprocess_har",
    "scan_file",
]
