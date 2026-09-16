"""Provider registration and credential routing, without API calls."""

from __future__ import annotations

import pytest

from harcompanon.config import DEFAULT_MAX_TOKENS, DEFAULT_MODELS, build_provider
from harcompanon.providers import (
    AnthropicProvider,
    GeminiProvider,
    OpenAICompatProvider,
    OpenAIProvider,
)


@pytest.mark.parametrize(
    ("name", "provider_type", "base_url", "key_env"),
    [
        ("anthropic", AnthropicProvider, None, None),
        ("openai", OpenAIProvider, None, None),
        ("gemini", GeminiProvider, None, None),
        ("deepseek", OpenAICompatProvider, "https://api.deepseek.com", "DEEPSEEK_API_KEY"),
        ("mistral", OpenAICompatProvider, "https://api.mistral.ai/v1", "MISTRAL_API_KEY"),
        ("kimi", OpenAICompatProvider, "https://api.moonshot.ai/v1", "MOONSHOT_API_KEY"),
    ],
)
def test_registry_routes_defaults_and_overrides(
    name: str,
    provider_type: type[AnthropicProvider | OpenAIProvider | GeminiProvider | OpenAICompatProvider],
    base_url: str | None,
    key_env: str | None,
) -> None:
    default = build_provider(name)
    custom = build_provider(name, model="custom-model", max_tokens=64000)
    assert isinstance(default, provider_type) and isinstance(custom, provider_type)
    assert default.name == custom.name == name
    assert default.model == DEFAULT_MODELS[name]
    assert default.max_tokens == DEFAULT_MAX_TOKENS
    assert custom.model == "custom-model" and custom.max_tokens == 64000
    if isinstance(default, OpenAICompatProvider):
        assert default.base_url == base_url
        assert default.api_key_env == key_env


@pytest.mark.parametrize("name", ["deepseek", "mistral", "kimi"])
def test_missing_vendor_key_never_falls_back_to_openai(
    name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = build_provider(name)
    assert isinstance(provider, OpenAICompatProvider)
    monkeypatch.delenv(provider.api_key_env, raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key-that-must-stay-with-openai")

    # A regression must fail locally instead of constructing a client or making a request.
    def unexpected_client(**kwargs: object) -> None:
        pytest.fail("Attempted to construct a client without the vendor's own key")

    monkeypatch.setattr("openai.OpenAI", unexpected_client)
    with pytest.raises(ValueError, match=provider.api_key_env):
        provider.complete("hello")


def test_unknown_provider_raises() -> None:
    with pytest.raises(ValueError, match="Unknown provider"):
        build_provider("does-not-exist")
