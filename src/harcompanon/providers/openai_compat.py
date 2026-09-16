"""Generic provider for OpenAI chat-completions-compatible APIs.

DeepSeek, Mistral, and Moonshot (Kimi) all expose an OpenAI-compatible ``chat/completions``
endpoint, so one class parameterised by base URL + key env var covers them all. Stateless,
no temperature (model default), SDK imported lazily — same shape as the other providers.

No explicit reasoning setting is sent; behavior depends on the selected model's defaults.
The adapter records reasoning tokens when the API reports them separately.
"""

from __future__ import annotations

import os
import time

from harcompanon.providers.base import RawResponse


class OpenAICompatProvider:
    """Calls an OpenAI-compatible chat API at ``base_url`` using ``api_key_env`` from the env."""

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key_env: str,
        model: str,
        max_tokens: int,
    ) -> None:
        self.name = name
        self.base_url = base_url
        self.api_key_env = api_key_env
        self.model = model
        self.max_tokens = max_tokens

    def complete(self, prompt: str) -> RawResponse:
        api_key = os.environ.get(self.api_key_env)
        if not api_key:
            # The SDK otherwise falls back to OPENAI_API_KEY, even for another vendor's URL.
            raise ValueError(f"Missing {self.api_key_env} for {self.name}.")

        from openai import OpenAI

        client = OpenAI(base_url=self.base_url, api_key=api_key)
        started = time.monotonic()
        completion = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.max_tokens,
        )
        latency_ms = (time.monotonic() - started) * 1000

        choices = getattr(completion, "choices", None) or []
        text = ""
        stop_reason = None
        if choices:
            text = getattr(choices[0].message, "content", "") or ""
            stop_reason = getattr(choices[0], "finish_reason", None)
        usage = getattr(completion, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", None)
        output_tokens = getattr(usage, "completion_tokens", None)
        # Reasoners (DeepSeek, Kimi) fold reasoning into completion_tokens; capture the breakdown
        # when the API exposes it so counts stay comparable with the other providers.
        details = getattr(usage, "completion_tokens_details", None)
        reasoning_tokens = getattr(details, "reasoning_tokens", None)
        model = getattr(completion, "model", self.model)
        return RawResponse(
            provider=self.name,
            model=model,
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            reasoning_tokens=reasoning_tokens,
            latency_ms=latency_ms,
            stop_reason=stop_reason,
        )
