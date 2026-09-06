"""Anthropic (Claude) provider — the reference implementation of the Provider protocol.

Stateless, single-shot ``messages.create`` calls. No temperature/top_p (defaults kept for
comparability). Extended thinking is enabled with ``type: "adaptive"`` so reasoning is ON,
matching the other providers in the equalized-reasoning configuration (``budget_tokens`` is
rejected on Opus 4.8, so adaptive is the only knob). The rendered prompt is sent as one user
message; the human judges the text.
"""

from __future__ import annotations

import time

from harcompanon.providers.base import RawResponse, estimate_cost

DEFAULT_MODEL = "claude-opus-4-8"
DEFAULT_MAX_TOKENS = 16000


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
        # Stream, so a large max_tokens can't hit the SDK's non-streaming timeout guard and a
        # long response is never cut short.
        with client.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            thinking={"type": "adaptive"},  # reasoning ON (equalized config)
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            message = stream.get_final_message()
        latency_ms = (time.monotonic() - started) * 1000

        # Extended thinking arrives as separate `thinking` blocks; the answer is the `text` blocks.
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
