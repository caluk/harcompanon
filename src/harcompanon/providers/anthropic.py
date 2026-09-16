"""Anthropic (Claude) provider — the reference implementation of the Provider protocol.

Stateless streaming messages calls with adaptive thinking and default sampling.
The rendered prompt is sent as one user message; the human judges the text.
Reasoning controls differ across providers and do not imply equal budgets.
"""

from __future__ import annotations

import time

from harcompanon.providers.base import RawResponse


class AnthropicProvider:
    """Calls Claude via the official ``anthropic`` SDK (reads ANTHROPIC_API_KEY from env)."""

    name = "anthropic"

    def __init__(self, model: str, max_tokens: int) -> None:
        self.model = model
        self.max_tokens = max_tokens

    def complete(self, prompt: str) -> RawResponse:
        import anthropic  # imported lazily so --dry-run and tests need no SDK/key

        client = anthropic.Anthropic()
        started = time.monotonic()
        # Streaming avoids the SDK's non-streaming timeout guard for large token budgets.
        with client.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            thinking={"type": "adaptive"},
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
            latency_ms=latency_ms,
            stop_reason=message.stop_reason,
        )
