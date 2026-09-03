"""Model providers behind one small protocol. Adding a model = one class + one registry entry."""

from __future__ import annotations

from harcompanon.providers.anthropic import AnthropicProvider
from harcompanon.providers.base import PRICING, Provider, RawResponse, estimate_cost
from harcompanon.providers.gemini import GeminiProvider
from harcompanon.providers.litellm_provider import LiteLLMProvider
from harcompanon.providers.openai import OpenAIProvider
from harcompanon.providers.openai_compat import OpenAICompatProvider

__all__ = [
    "PRICING",
    "AnthropicProvider",
    "GeminiProvider",
    "LiteLLMProvider",
    "OpenAICompatProvider",
    "OpenAIProvider",
    "Provider",
    "RawResponse",
    "estimate_cost",
]
