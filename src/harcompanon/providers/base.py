"""Provider abstraction: one seam every model plugs into.

A ``Provider`` takes a fully-rendered prompt and returns a ``RawResponse`` (text + usage +
latency). Adding a model is one new class implementing this protocol plus one registry entry —
nothing else in the pipeline knows which provider it is talking to. Calls are stateless and
single-shot; provider deployments and defaults can still change between runs.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel


class RawResponse(BaseModel):
    """What a provider returns for one prompt — the unit the human later judges."""

    provider: str
    model: str
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    #: Reasoning/"thinking" tokens, when the provider reports them separately, so the
    #: reader can distinguish providers that account for reasoning differently
    #: (some fold it into output_tokens; Gemini reports it apart as thoughts). None = not reported.
    reasoning_tokens: int | None = None
    latency_ms: float = 0.0
    stop_reason: str | None = None


@runtime_checkable
class Provider(Protocol):
    """A stateless, single-shot completion source. Implementations live in this package."""

    name: str
    model: str

    def complete(self, prompt: str) -> RawResponse: ...
