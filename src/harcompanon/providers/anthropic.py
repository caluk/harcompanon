"""Anthropic (Claude) provider — the reference implementation of the Provider protocol.

Stateless, single-shot ``messages.create`` calls. No temperature/top_p/budget_tokens: those
are rejected on current Opus models, and leaving sampling at the default keeps runs
comparable. The rendered prompt is sent as one user message; the human judges the text.
"""

from __future__ import annotations

import time

from harcompanon.providers.base import RawResponse, estimate_cost

DEFAULT_MODEL = "claude-opus-4-8"
DEFAULT_MAX_TOKENS = 8192


class AnthropicProvider:
    """Calls Claude via the official ``anthropic`` SDK (reads ANTHROPIC_API_KEY from env)."""

    name = "anthropic"

    def __init__(self, model: str = DEFAULT_MODEL, max_tokens: int = DEFAULT_MAX_TOKENS) -> None:
        self.model = model
        self.max_tokens = max_tokens

    def complete(self, prompt: str) -> RawResponse:
        import anthropic  # imported lazily so --dry-run and tests need no SDK/key

        client = anthropic.Anthropic()
        started = time.monotonic()
        message = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        latency_ms = (time.monotonic() - started) * 1000

        text = "".join(
            getattr(block, "text", "")
            for block in message.content
            if getattr(block, "type", None) == "text"
        )
        usage = message.usage
        return RawResponse(
            provider=self.name,
            model=message.model,
            text=text,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            cost_usd=estimate_cost(message.model, usage.input_tokens, usage.output_tokens),
            latency_ms=latency_ms,
            stop_reason=message.stop_reason,
        )
