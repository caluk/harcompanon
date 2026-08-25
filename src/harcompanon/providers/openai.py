"""OpenAI provider — same Provider protocol as Anthropic, different SDK.

Stateless single-shot call via the Responses API. No temperature (kept at the model default,
matching the Anthropic provider for cross-provider comparability). The SDK is imported lazily
so --dry-run and tests need neither the package nor a key.
"""

from __future__ import annotations

import time

from harcompanon.providers.base import RawResponse, estimate_cost

DEFAULT_MODEL = "gpt-5"
DEFAULT_MAX_TOKENS = 16000


class OpenAIProvider:
    """Calls OpenAI via the official ``openai`` SDK (reads OPENAI_API_KEY from env)."""

    name = "openai"

    def __init__(self, model: str = DEFAULT_MODEL, max_tokens: int = DEFAULT_MAX_TOKENS) -> None:
        self.model = model
        self.max_tokens = max_tokens

    def complete(self, prompt: str) -> RawResponse:
        from openai import OpenAI

        client = OpenAI()
        started = time.monotonic()
        response = client.responses.create(
            model=self.model,
            input=prompt,
            max_output_tokens=self.max_tokens,
        )
        latency_ms = (time.monotonic() - started) * 1000

        text = getattr(response, "output_text", "") or ""
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", None)
        output_tokens = getattr(usage, "output_tokens", None)
        model = getattr(response, "model", self.model)
        return RawResponse(
            provider=self.name,
            model=model,
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=estimate_cost(model, input_tokens, output_tokens),
            latency_ms=latency_ms,
            stop_reason=getattr(response, "status", None),
        )
