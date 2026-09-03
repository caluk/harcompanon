"""OPTIONAL, EXPLORATORY backend — route every provider through LiteLLM instead of each vendor SDK.

This exists for **learning / for fun**, not because the tool needs it. The default, supported path
is the native per-vendor providers (``anthropic.py``, ``openai.py``, ``gemini.py``,
``openai_compat.py``); this is opt-in via ``--backend litellm`` and the ``litellm`` extra
(``pip install -e ".[litellm]"``). Nothing else in the pipeline changes — that's the whole point.

LiteLLM (https://github.com/BerriAI/litellm) is a thin *adapter*: one ``completion()`` call in the
OpenAI message format, translated to 100+ providers. So this single class stands in for all four
native provider modules — a neat demonstration of why the ``Provider`` protocol is the right seam,
and of what you trade (explicit per-vendor control) for uniformity. See ``docs/litellm-backend.md``.

Security: API keys are read from the environment (the same git-ignored ``.env``), never passed as
arguments and never logged. LiteLLM's anonymous telemetry is turned off, and nothing here logs the
prompt, the response, or any credential.
"""

from __future__ import annotations

import time

from harcompanon.providers.base import RawResponse, estimate_cost

#: harcompañon provider name -> LiteLLM route prefix. LiteLLM routes on ``"<prefix>/<model>"`` and
#: reads each provider's standard key env var (ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY,
#: DEEPSEEK_API_KEY, MISTRAL_API_KEY, MOONSHOT_API_KEY) — exactly the ones already in ``.env``.
LITELLM_ROUTES: dict[str, str] = {
    "anthropic": "anthropic",
    "openai": "openai",
    "gemini": "gemini",
    "deepseek": "deepseek",
    "mistral": "mistral",
    "kimi": "moonshot",
}


class LiteLLMProvider:
    """Same ``Provider`` protocol; every call goes through LiteLLM's uniform ``completion()``."""

    def __init__(self, name: str, model: str, max_tokens: int, route: str | None = None) -> None:
        self.name = name
        self.model = model
        self.max_tokens = max_tokens
        #: The string LiteLLM routes on, e.g. ``"anthropic/claude-opus-4-8"``.
        self.litellm_model = f"{route or LITELLM_ROUTES.get(name, name)}/{model}"

    def complete(self, prompt: str) -> RawResponse:
        import litellm

        litellm.telemetry = False  # do not phone home from a published repo

        started = time.monotonic()
        response = litellm.completion(
            model=self.litellm_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.max_tokens,
        )
        latency_ms = (time.monotonic() - started) * 1000

        choices = getattr(response, "choices", None) or []
        text = ""
        stop_reason = None
        if choices:
            text = getattr(choices[0].message, "content", "") or ""
            stop_reason = getattr(choices[0], "finish_reason", None)
        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", None)
        output_tokens = getattr(usage, "completion_tokens", None)

        # LiteLLM can price most models itself; fall back to our own table for anything it doesn't
        # recognise (e.g. a very new flagship id it hasn't shipped pricing for yet).
        cost = _litellm_cost(response)
        if cost is None:
            cost = estimate_cost(self.model, input_tokens, output_tokens)

        return RawResponse(
            provider=self.name,
            model=self.model,
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
            stop_reason=stop_reason,
        )


def _litellm_cost(response: object) -> float | None:
    try:
        import litellm

        return float(litellm.completion_cost(completion_response=response))
    except Exception:
        return None
