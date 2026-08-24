"""Provider abstraction: one seam every model plugs into.

A ``Provider`` takes a fully-rendered prompt and returns a ``RawResponse`` (text + usage +
cost + latency). Adding a model is one new class implementing this protocol plus one registry
entry — nothing else in the pipeline knows which provider it is talking to. Calls are
stateless and single-shot, so reruns are comparable months apart.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel

#: Per-model price in USD per 1M tokens: (input, output). Prices drift — revisit periodically.
PRICING: dict[str, tuple[float, float]] = {
    "claude-opus-4-8": (5.0, 25.0),
    "claude-opus-4-7": (5.0, 25.0),
    "claude-sonnet-5": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
}


def estimate_cost(model: str, input_tokens: int | None, output_tokens: int | None) -> float | None:
    """USD cost from token usage, or None if the model's price isn't known."""
    price = PRICING.get(model)
    if price is None or input_tokens is None or output_tokens is None:
        return None
    return input_tokens / 1_000_000 * price[0] + output_tokens / 1_000_000 * price[1]


class RawResponse(BaseModel):
    """What a provider returns for one prompt — the unit the human later judges."""

    provider: str
    model: str
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    latency_ms: float = 0.0
    stop_reason: str | None = None


@runtime_checkable
class Provider(Protocol):
    """A stateless, single-shot completion source. Implementations live in this package."""

    name: str
    model: str

    def complete(self, prompt: str) -> RawResponse: ...
