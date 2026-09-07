"""Flat-file storage for a run: per-response JSON plus the run manifest. No database.

``run.json`` is the source of truth (``load_run`` reads it back; ``compare`` renders from it);
each response is also written as its own JSON for easy inspection.
"""

from __future__ import annotations

import json
from pathlib import Path

from harcompanon.execution import RunResult


def store_run(run: RunResult, out_dir: Path) -> Path:
    """Write the run under ``out_dir/<run_id>/`` and return that directory."""
    run_dir = out_dir / run.run_id
    responses_dir = run_dir / "responses"
    responses_dir.mkdir(parents=True, exist_ok=True)

    for item in run.responses:
        name = f"{item.provider}__{item.mode}.json"
        payload = item.model_dump(mode="json")
        (responses_dir / name).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    (run_dir / "run.json").write_text(run.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return run_dir


def load_run(run_dir: Path) -> RunResult:
    """Load a stored run back into a RunResult (from ``run.json``)."""
    run_json = run_dir / "run.json"
    if not run_json.is_file():
        raise ValueError(f"{run_dir} is not a run directory (no run.json).")
    return RunResult.model_validate_json(run_json.read_text(encoding="utf-8"))
