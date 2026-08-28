"""Execution orchestrator.

A *run* = one frozen fixture x all configured providers x the chosen prompt modes. The fixture
is preprocessed once, each mode's prompt is rendered from the cleaned evidence, and every
(provider, mode) pair is a stateless call. A ``--dry-run`` renders the prompts and exercises
the whole pipeline without spending a token, so everything is testable without API keys.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from harcompanon.preprocess import preprocess_file
from harcompanon.prompts import render_prompt
from harcompanon.providers import Provider, RawResponse

DRY_RUN_TEXT = "[dry-run — prompt rendered, no API call made]"

#: Run timestamps are stamped in Central European Time for human readability.
_TZ = ZoneInfo("Europe/Berlin")
# Only strip the verbose Anthropic prefix; gpt-5 / gemini-2.5-pro stay readable as-is.
_VENDOR_PREFIXES = ("claude-", "models/")


def _slugify(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "x"


def _model_slug(providers: list[Provider]) -> str:
    """A compact, filename-safe token naming the model(s) that ran."""
    seen: list[str] = []
    for provider in providers:
        model = provider.model
        for prefix in _VENDOR_PREFIXES:
            model = model.removeprefix(prefix)
        slug = _slugify(model)
        if slug not in seen:
            seen.append(slug)
    if len(seen) == 1:
        return seen[0]
    if len(seen) <= 3:
        return "+".join(seen)
    return f"{len(seen)}models"


def build_run_id(fixture: Path, providers: list[Provider], now: datetime) -> str:
    """e.g. ``dash_opus-4-8_2026-08-24_12-53-24`` — fixture, model(s), CET time; OS-safe."""
    return f"{_slugify(fixture.stem)}_{_model_slug(providers)}_{now:%Y-%m-%d_%H-%M-%S}"


class RunResponse(BaseModel):
    """One (provider, mode) result plus the metadata needed to compare and reproduce it."""

    provider: str
    model: str
    mode: str
    version: str
    prompt_chars: int
    dry_run: bool
    error: str | None
    response: RawResponse


class RunResult(BaseModel):
    """Everything produced by a single run — the comparison surface's source of truth."""

    run_id: str
    fixture: str
    created_at: str
    dry_run: bool
    providers: list[str]
    modes: list[str]
    responses: list[RunResponse]


def run_benchmark(
    fixture: Path,
    providers: list[Provider],
    modes: list[str],
    *,
    version: str = "v2",
    dry_run: bool = False,
    on_response: Callable[[RunResponse, int, int], None] | None = None,
) -> RunResult:
    """Run the fixture through every provider at every mode and collect the responses.

    ``on_response`` (if given) is called after each (provider, mode) completes with the response
    and its 1-based position / total, so a caller can stream progress during a long live run.
    """
    artifact_json = preprocess_file(fixture).to_canonical_json()
    now = datetime.now(_TZ)
    created_at = now.isoformat(timespec="seconds")
    run_id = build_run_id(fixture, providers, now)

    total = len(modes) * len(providers)
    responses: list[RunResponse] = []
    for mode in modes:
        prompt = render_prompt(mode, artifact_json, version)
        for provider in providers:
            result = _one(provider, mode, version, prompt, dry_run=dry_run)
            responses.append(result)
            if on_response is not None:
                on_response(result, len(responses), total)

    return RunResult(
        run_id=run_id,
        fixture=fixture.name,
        created_at=created_at,
        dry_run=dry_run,
        providers=[p.name for p in providers],
        modes=list(modes),
        responses=responses,
    )


def retry_failed(
    run: RunResult,
    fixture: Path,
    build: Callable[[str, str], Provider],
    *,
    should_retry: Callable[[RunResponse], bool] | None = None,
    on_response: Callable[[RunResponse, int, int], None] | None = None,
) -> RunResult:
    """Re-call the (provider, mode) pairs a run needs redone, and return the patched result.

    ``should_retry`` selects which responses to redo (default: only errored ones). The caller can
    widen it — e.g. to also redo a structured response that came back missing sections (a truncated
    or stunted answer). ``build(provider_name, model)`` returns a ready provider; the fixture is
    re-preprocessed and each pair's prompt re-rendered, so the result is back-filled into the *same*
    run rather than spawning a separate one. Responses that don't match are left as-is.
    """
    should_retry = should_retry or (lambda r: bool(r.error))
    artifact_json = preprocess_file(fixture).to_canonical_json()
    prompts: dict[str, str] = {}
    responses = list(run.responses)
    failed = [i for i, r in enumerate(responses) if should_retry(r)]
    for done, index in enumerate(failed, start=1):
        item = responses[index]
        prompt = prompts.setdefault(
            item.mode, render_prompt(item.mode, artifact_json, item.version)
        )
        result = _one(
            build(item.provider, item.model), item.mode, item.version, prompt, dry_run=False
        )
        responses[index] = result
        if on_response is not None:
            on_response(result, done, len(failed))
    return run.model_copy(update={"responses": responses})


def _one(
    provider: Provider,
    mode: str,
    version: str,
    prompt: str,
    *,
    dry_run: bool,
) -> RunResponse:
    error: str | None = None
    if dry_run:
        response = RawResponse(provider=provider.name, model=provider.model, text=DRY_RUN_TEXT)
    else:
        try:
            response = provider.complete(prompt)
        except Exception as exc:  # one provider failing must not sink the whole run
            error = f"{type(exc).__name__}: {exc}"
            response = RawResponse(provider=provider.name, model=provider.model, text="")
    return RunResponse(
        provider=provider.name,
        model=provider.model,
        mode=mode,
        version=version,
        prompt_chars=len(prompt),
        dry_run=dry_run,
        error=error,
        response=response,
    )
