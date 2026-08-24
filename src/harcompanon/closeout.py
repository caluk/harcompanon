"""Generate a session close-out scaffold from the five RST debrief questions.

Pre-filled with the run's metadata; the human writes the debrief. The five questions come from
session-based test management: what did you do, how did it go, did you notice problems, how did
you evaluate them, now what.
"""

from __future__ import annotations

from harcompanon.execution import RunResult


def generate_closeout(run: RunResult) -> str:
    """Return the close-out markdown scaffold for ``run`` (the human writes the answers)."""
    total_cost = sum(r.response.cost_usd or 0.0 for r in run.responses)
    cost_line = f"- Total cost: ${total_cost:.4f}" if total_cost else "- Total cost: —"
    lines = [
        f"# Session close-out — {run.run_id}",
        "",
        "## Metadata",
        f"- Fixture: `{run.fixture}`",
        f"- Providers: {', '.join(run.providers)}",
        f"- Modes: {', '.join(run.modes)}",
        f"- Responses: {len(run.responses)}",
        f"- Created: {run.created_at}",
        cost_line,
        "",
        "> RST session-based debrief. You are the sole judge — write the answers below.",
        "",
        "## 1. What did you do?",
        f"Ran `{run.fixture}` through {', '.join(run.providers)} "
        f"at prompt modes: {', '.join(run.modes)}.",
        "",
        "## 2. How did it go?",
        "",
        "## 3. Did you notice specific problems?",
        "_(in the fixture itself, and in how each companion behaved)_",
        "",
        "## 4. How did you evaluate them?",
        "_(see the judgment file: oracle named? defensible? ladder position per finding)_",
        "",
        "## 5. Now what?",
        "",
    ]
    return "\n".join(lines) + "\n"
