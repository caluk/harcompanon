"""Google Gemini provider — same Provider protocol, different SDK.

Stateless single-shot call via the ``google-genai`` SDK. No temperature (model default), for
cross-provider comparability. The SDK is imported lazily so --dry-run and tests need neither
the package nor a key.
"""

from __future__ import annotations

import os
import time

from harcompanon.providers.base import RawResponse, estimate_cost

DEFAULT_MODEL = "gemini-2.5-pro"
DEFAULT_MAX_TOKENS = 16000


class GeminiProvider:
    """Calls Gemini via ``google-genai`` (reads GEMINI_API_KEY or GOOGLE_API_KEY from env)."""

    name = "gemini"

    def __init__(self, model: str = DEFAULT_MODEL, max_tokens: int = DEFAULT_MAX_TOKENS) -> None:
        self.model = model
        self.max_tokens = max_tokens

    def complete(self, prompt: str) -> RawResponse:
        from google import genai
        from google.genai import types

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)
        started = time.monotonic()
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(max_output_tokens=self.max_tokens),
        )
        latency_ms = (time.monotonic() - started) * 1000

        text = getattr(response, "text", "") or ""
        usage = getattr(response, "usage_metadata", None)
        input_tokens = getattr(usage, "prompt_token_count", None)
        output_tokens = getattr(usage, "candidates_token_count", None)
        return RawResponse(
            provider=self.name,
            model=self.model,
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=estimate_cost(self.model, input_tokens, output_tokens),
            latency_ms=latency_ms,
            stop_reason=None,
        )
