"""Google Gemini provider — same Provider protocol, different SDK.

Stateless single-shot call via the ``google-genai`` SDK. No temperature (model default), for
cross-provider comparability. Thinking is set to a dynamic budget (``thinking_budget=-1``) so
reasoning is ON and model-decided, matching the other providers in the equalized-reasoning
configuration. The thinking tokens are reported apart from the visible output (as
``thoughts_token_count``) and captured into ``reasoning_tokens`` so counts stay comparable. The
SDK is imported lazily so --dry-run and tests need neither the package nor a key.
"""

from __future__ import annotations

import logging
import os
import time

from harcompanon.providers.base import RawResponse


class GeminiProvider:
    """Calls Gemini via ``google-genai`` (reads GEMINI_API_KEY or GOOGLE_API_KEY from env)."""

    name = "gemini"

    def __init__(self, model: str, max_tokens: int) -> None:
        self.model = model
        self.max_tokens = max_tokens

    def complete(self, prompt: str) -> RawResponse:
        from google import genai
        from google.genai import types

        # The SDK logs a spurious "direct use of automatic function calling (AFC)" warning on
        # every generate_content call, even though we pass no tools. Silence just that logger.
        logging.getLogger("google_genai.models").setLevel(logging.ERROR)

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        client = genai.Client(api_key=api_key)
        started = time.monotonic()
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=self.max_tokens,
                # Dynamic thinking budget: reasoning ON, model decides depth (equalized config).
                thinking_config=types.ThinkingConfig(thinking_budget=-1),
            ),
        )
        latency_ms = (time.monotonic() - started) * 1000

        text = getattr(response, "text", "") or ""
        usage = getattr(response, "usage_metadata", None)
        input_tokens = getattr(usage, "prompt_token_count", None)
        # candidates_token_count = visible output; thoughts_token_count = reasoning, reported apart.
        output_tokens = getattr(usage, "candidates_token_count", None)
        reasoning_tokens = getattr(usage, "thoughts_token_count", None)
        return RawResponse(
            provider=self.name,
            model=self.model,
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            reasoning_tokens=reasoning_tokens,
            latency_ms=latency_ms,
            stop_reason=None,
        )
