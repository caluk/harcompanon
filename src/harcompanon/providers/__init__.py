"""Model providers behind one small protocol. Adding a model = one class + one registry entry."""

from __future__ import annotations

from harcompanon.providers.anthropic import AnthropicProvider
from harcompanon.providers.base import Provider, RawResponse
from harcompanon.providers.gemini import GeminiProvider
from harcompanon.providers.openai import OpenAIProvider
from harcompanon.providers.openai_compat import OpenAICompatProvider

__all__ = [
    "AnthropicProvider",
    "GeminiProvider",
    "OpenAICompatProvider",
    "OpenAIProvider",
    "Provider",
    "RawResponse",
]
