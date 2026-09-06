"""Conventional software tests (pytest) for the provider abstraction and registry."""

from __future__ import annotations

import pytest

from harcompanon.config import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODELS,
    available_providers,
    build_provider,
)
from harcompanon.providers import (
    AnthropicProvider,
    GeminiProvider,
    OpenAICompatProvider,
    OpenAIProvider,
    Provider,
    RawResponse,
    estimate_cost,
)


def test_estimate_cost_known_and_unknown() -> None:
    # claude-opus-4-8 is $5/$25 per 1M tokens.
    assert estimate_cost("claude-opus-4-8", 1_000_000, 1_000_000) == pytest.approx(30.0)
    assert estimate_cost("claude-opus-4-8", None, 10) is None
    assert estimate_cost("some-unpriced-model", 100, 100) is None


def test_estimate_cost_normalizes_dated_model_id() -> None:
    # The API can return a dated snapshot; pricing is keyed on the alias.
    assert estimate_cost("claude-haiku-4-5-20251001", 1_000_000, 1_000_000) == pytest.approx(6.0)


def test_registry_builds_anthropic_with_default_model() -> None:
    assert "anthropic" in available_providers()
    provider = build_provider("anthropic")
    assert isinstance(provider, AnthropicProvider)
    assert provider.model == "claude-opus-4-8"
    assert build_provider("anthropic", model="claude-haiku-4-5").model == "claude-haiku-4-5"


def test_max_tokens_is_configurable_and_defaults_to_32000() -> None:
    default = build_provider("anthropic")
    custom = build_provider("anthropic", max_tokens=64000)
    assert isinstance(default, AnthropicProvider) and default.max_tokens == DEFAULT_MAX_TOKENS
    assert default.max_tokens == 32000
    assert isinstance(custom, AnthropicProvider) and custom.max_tokens == 64000


def test_registry_has_all_three_providers() -> None:
    assert set(available_providers()) >= {"anthropic", "openai", "gemini"}
    openai = build_provider("openai")
    gemini = build_provider("gemini")
    assert isinstance(openai, OpenAIProvider)
    assert openai.model == DEFAULT_MODELS["openai"]
    assert isinstance(gemini, GeminiProvider)
    assert gemini.model == DEFAULT_MODELS["gemini"]
    # Both satisfy the runtime_checkable protocol without importing their SDKs.
    assert isinstance(openai, Provider)
    assert isinstance(gemini, Provider)


def test_openai_compatible_providers_are_registered() -> None:
    assert {"deepseek", "mistral", "kimi"} <= set(available_providers())
    deepseek = build_provider("deepseek")
    assert isinstance(deepseek, OpenAICompatProvider)
    assert deepseek.name == "deepseek"
    assert deepseek.base_url == "https://api.deepseek.com"
    assert deepseek.api_key_env == "DEEPSEEK_API_KEY"
    assert deepseek.model == DEFAULT_MODELS["deepseek"]
    assert isinstance(deepseek, Provider)
    # override model + other vendors resolve their own base url / env
    assert build_provider("kimi", model="kimi-x").model == "kimi-x"
    mistral = build_provider("mistral")
    assert isinstance(mistral, OpenAICompatProvider)
    assert mistral.base_url == "https://api.mistral.ai/v1"


def test_unknown_provider_raises() -> None:
    with pytest.raises(ValueError, match="Unknown provider"):
        build_provider("does-not-exist")


def test_anthropic_provider_satisfies_protocol() -> None:
    # runtime_checkable Protocol: name, model, complete().
    assert isinstance(AnthropicProvider("claude-opus-4-8", 32000), Provider)


def test_raw_response_round_trips() -> None:
    r = RawResponse(provider="anthropic", model="claude-opus-4-8", text="hi", input_tokens=3)
    assert r.model_dump()["text"] == "hi"
    assert r.output_tokens is None
