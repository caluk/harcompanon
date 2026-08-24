"""Execution orchestrator.

A *run* = one frozen fixture x all configured providers x the chosen prompt modes. The fixture
is preprocessed once, each mode's prompt is rendered from the cleaned evidence, and every
(provider, mode) pair is a stateless call. A ``--dry-run`` renders the prompts and exercises
the whole pipeline without spending a token, so everything is testable without API keys.
"""

from __future__ import annotations

import re
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
_VENDOR_PREFIXES = ("claude-", "gpt-", "gemini-", "models/")


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
    version: str = "v1",
    dry_run: bool = False,
) -> RunResult:
    """Run the fixture through every provider at every mode and collect the responses."""
    artifact_json = preprocess_file(fixture).to_canonical_json()
    now = datetime.now(_TZ)
    created_at = now.isoformat(timespec="seconds")
    run_id = build_run_id(fixture, providers, now)

    responses: list[RunResponse] = []
    for mode in modes:
        prompt = render_prompt(mode, artifact_json, version)
        for provider in providers:
            responses.append(_one(provider, mode, version, prompt, dry_run=dry_run))

    return RunResult(
        run_id=run_id,
        fixture=fixture.name,
        created_at=created_at,
        dry_run=dry_run,
        providers=[p.name for p in providers],
        modes=list(modes),
        responses=responses,
    )


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
