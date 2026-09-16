"""Conventional software tests (pytest) for execution + storage, using a fake provider.

No API keys or network — a FakeProvider stands in for a real model, and --dry-run exercises
the pipeline with no provider call at all.
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from harcompanon.cli import app
from harcompanon.execution import DRY_RUN_TEXT, run_benchmark
from harcompanon.providers import RawResponse
from harcompanon.storage import load_run, store_run

SAMPLE = Path(__file__).parents[1] / "data" / "sample.har"
runner = CliRunner()


class FakeProvider:
    name = "fake"
    model = "fake-1"

    def __init__(self, *, boom: bool = False, name: str = "fake") -> None:
        self.boom = boom
        self.name = name
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> RawResponse:
        self.prompts.append(prompt)
        if self.boom:
            raise RuntimeError("no network")
        return RawResponse(
            provider=self.name,
            model=self.model,
            text=f"seen {len(prompt)} chars",
            input_tokens=10,
            output_tokens=5,
            latency_ms=1.0,
        )


def test_run_sends_identical_prompts_to_each_provider() -> None:
    first, second = FakeProvider(), FakeProvider(name="other")
    result = run_benchmark(SAMPLE, [first, second], ["minimal", "structured"])
    assert result.run_id.startswith("sample_fake-1_")
    assert [(r.provider, r.mode) for r in result.responses] == [
        ("fake", "minimal"),
        ("other", "minimal"),
        ("fake", "structured"),
        ("other", "structured"),
    ]
    assert first.prompts == second.prompts
    assert len(first.prompts) == 2 and first.prompts[0] != first.prompts[1]
    for r in result.responses:
        assert r.error is None
        assert r.response.text == f"seen {r.prompt_chars} chars"


def test_dry_run_makes_no_call() -> None:
    provider = FakeProvider(boom=True)
    result = run_benchmark(SAMPLE, [provider], ["minimal"], dry_run=True)
    assert provider.prompts == []
    assert result.responses[0].response.text == DRY_RUN_TEXT
    assert result.responses[0].error is None


def test_provider_error_is_captured_not_raised() -> None:
    result = run_benchmark(SAMPLE, [FakeProvider(boom=True), FakeProvider(name="ok")], ["minimal"])
    item = result.responses[0]
    assert item.error is not None
    assert "no network" in item.error
    assert item.response.text == ""
    assert result.responses[1].error is None
    assert result.responses[1].response.text.startswith("seen ")


def test_store_run_writes_json(tmp_path: Path) -> None:
    result = run_benchmark(SAMPLE, [FakeProvider()], ["minimal", "structured"])
    run_dir = store_run(result, tmp_path)
    assert load_run(run_dir) == result
    for response in result.responses:
        saved = run_dir / "responses" / f"fake__{response.mode}.json"
        assert type(response).model_validate_json(saved.read_text()) == response


def test_cli_run_dry_run(tmp_path: Path) -> None:
    result = runner.invoke(app, ["run", str(SAMPLE), "--dry-run", "--out", str(tmp_path)])
    assert result.exit_code == 0, result.output
    run_dirs = list(tmp_path.iterdir())
    assert len(run_dirs) == 1
    saved = load_run(run_dirs[0])
    assert saved.dry_run
    assert {r.mode for r in saved.responses} == {"minimal", "structured"}
    assert all(r.version == "v5" and r.error is None for r in saved.responses)


def test_cli_run_rejects_unknown_mode(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["run", str(SAMPLE), "--dry-run", "--modes", "bogus", "--out", str(tmp_path)]
    )
    assert result.exit_code == 2
    assert "Unknown mode" in result.output


def test_retry_only_touches_failed_responses() -> None:
    from harcompanon.execution import retry_failed

    result = run_benchmark(SAMPLE, [FakeProvider(boom=True)], ["minimal", "structured"])
    assert all(r.error for r in result.responses)  # both failed (no network)
    # Pretend the first one had actually succeeded on the original run.
    kept = result.responses[0].response.model_copy(update={"text": "KEEP ME"})
    ok = result.responses[0].model_copy(update={"error": None, "response": kept})
    result = result.model_copy(update={"responses": [ok, result.responses[1]]})

    patched = retry_failed(result, SAMPLE, lambda name, model: FakeProvider())
    assert patched.run_id == result.run_id  # same run identity
    assert patched.responses[0].response.text == "KEEP ME"  # success left untouched
    assert patched.responses[1].error is None  # failure re-run and fixed
    assert patched.responses[1].response.text


def test_retry_redoes_responses_matching_predicate() -> None:
    from harcompanon.execution import retry_failed

    result = run_benchmark(SAMPLE, [FakeProvider()], ["minimal", "structured"])
    # One response is "complete"; the other is an incomplete stub the predicate flags for redo.
    done = result.responses[0].model_copy(
        update={"response": result.responses[0].response.model_copy(update={"text": "COMPLETE"})}
    )
    stub = result.responses[1].model_copy(
        update={"response": result.responses[1].response.model_copy(update={"text": "stub"})}
    )
    result = result.model_copy(update={"responses": [done, stub]})

    patched = retry_failed(
        result,
        SAMPLE,
        lambda name, model: FakeProvider(),
        should_retry=lambda r: "COMPLETE" not in r.response.text,
    )
    assert patched.responses[0].response.text == "COMPLETE"  # complete one kept
    assert patched.responses[1].response.text.startswith("seen ")  # incomplete one redone


def test_cli_retry_noop_when_clean(tmp_path: Path) -> None:
    result = run_benchmark(SAMPLE, [FakeProvider()], ["minimal"])
    run_dir = store_run(result, tmp_path)
    out = runner.invoke(app, ["retry", str(run_dir)])
    assert out.exit_code == 0, out.output
    assert "Nothing to redo" in out.output
